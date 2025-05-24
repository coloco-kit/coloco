import aerich
import aerich.migrate

from aerich import Command
from aerich.models import Aerich
from aerich.migrate import Migrate
from aerich.utils import get_app_connection, get_models_describe
from .api import _verify_app
from ..app import ColocoApp, get_current_app
from ..db import app_class_to_table_name
from asyncio import run
import functools
import os
from pathlib import Path
from rich import print

from tortoise import generate_schema_for_client, Tortoise
from tortoise.exceptions import OperationalError
import typer


app = typer.Typer()

# ----------------------------- Monkey Patching -----------------------------
# TODO: Propose a patch to aerich to make migration location more configurable
_monkey_patched = False


def patch_migration_location(migrations_dir: str):
    global _monkey_patched
    if not _monkey_patched:

        def patched_path(*args, **kwargs):
            if len(args) == 2 and args[0] == migrations_dir:
                return Path("src", "app", args[1], args[0], **kwargs)
            else:
                return Path(*args, **kwargs)

        aerich.Path = patched_path
        aerich.migrate.Path = patched_path

        _monkey_patched = True


# ----------------------------- /Monkey Patching -----------------------------


def get_coloco_app():
    _verify_app()
    return get_current_app()


def get_model_apps(coloco_app: ColocoApp):
    return [app for app in coloco_app.orm_config["apps"] if app != "models"]


async def get_command(
    app: str = "models", coloco_app: ColocoApp = None, init: bool = True
):
    patch_migration_location(coloco_app.migrations_dir)
    coloco_app = coloco_app or get_coloco_app()
    command = Command(
        tortoise_config=coloco_app.orm_config,
        app=app,
        location=coloco_app.migrations_dir,
    )
    if init:
        await command.init()
        # TODO: propose a better way to do this
        Tortoise.table_name_generator = app_class_to_table_name
    return command


def get_app_migrations_path(app, migrations_dir: str) -> Path:
    return Path(os.path.join("src", "app", app, migrations_dir))


def ensure_app_migrations_dir(app, migrations_dir: str) -> bool:
    app_migrations_path = get_app_migrations_path(app, migrations_dir)
    if not app_migrations_path.exists():
        app_migrations_path.mkdir(parents=True, exist_ok=True)
        return False
    return True


async def has_migrations_inited(app: str, coloco_app: ColocoApp) -> bool:
    try:
        any_migrations = await Aerich.filter(app=app).first()
        return bool(any_migrations)
    except OperationalError as e:
        return False


class InitTortoise(Tortoise):
    pass


async def ensure_migrations_init(coloco_app: ColocoApp, safe=False):
    """
    Ensure that we have all initial migrations set up
    Iterates through apps and creates a blank initial migration.
    Aerich table is created under the app "models" and has the table initialized.
    """
    app = "models"

    await Tortoise.init(
        config=coloco_app.orm_config, table_name_generator=app_class_to_table_name
    )

    # Ensure we create aerich first
    app_list = ["models", *get_model_apps(coloco_app)]
    for app in app_list:
        has_migrations = await has_migrations_inited(app, coloco_app)
        if not has_migrations:
            all_apps = Tortoise.apps
            single_app = {app: all_apps[app]} if app == "models" else {app: {}}
            print(
                f" |- Initializing migrations for [yellow]{app}...[/yellow]",
                end="",
                flush=True,
            )
            connection = get_app_connection(coloco_app.orm_config, app)

            Tortoise.apps = single_app

            # Create initial aerich table
            if app == "models":
                await generate_schema_for_client(connection, safe)

            Migrate.app = app
            version = await Migrate.generate_version()
            await Aerich.create(
                version=version, app=app, content=get_models_describe(app)
            )

            Tortoise.apps = all_apps

            print("[green]OK[/green]")

    return has_migrations


def db_command(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        run(func(*args, **kwargs))
        run(Tortoise.close_connections())

    return wrapper


# ----------------------------- Commands -----------------------------


@app.command()
@db_command
async def makemigrations(app: str = None):
    coloco_app = get_coloco_app()
    apps = [app] if app else get_model_apps(coloco_app)

    await ensure_migrations_init(coloco_app)

    total = 0
    print("[yellow]Making migrations for all apps...[/yellow]")
    for app in apps:
        print(f" |- [yellow]{app}[/yellow] - ", end="", flush=True)
        ensure_app_migrations_dir(app, coloco_app.migrations_dir)
        command = await get_command(app, coloco_app)

        # TODO: ensure no unran migrations exist - they will be overrwitten

        # TODO: submit patch for aerich migration cleanup
        Migrate.upgrade_operators = []
        Migrate.downgrade_operators = []

        # TODO: better default name?
        migrations = await command.migrate(name="update", empty=False)

        if migrations:
            total += 1
            print("[green]changes detected[/green]")
        else:
            print("[gray]no changes[/gray]")

    if total:
        print(f"[green]{total}[/green] migration{'s' if total > 1 else ''} created.")
    else:
        print("No changes found.")


@app.command()
@db_command
async def migrate(app: str = None):
    coloco_app = get_coloco_app()
    apps = [app] if app else get_model_apps(coloco_app)

    await ensure_migrations_init(coloco_app)

    # TODO: do we need to combine these together for proper handling of foreign key relationships?
    #       ex: app1.Table1 has a field that references app2.Table2 - does table2 need to be created first?
    total = 0
    print("[cyan]Running migrations for all apps...[/cyan]")
    for app in apps:
        print(f" |- [cyan]{app}[/cyan] - ", end="", flush=True)
        ensure_app_migrations_dir(app, coloco_app.migrations_dir)
        command = await get_command(app, coloco_app)
        migrations = await command.upgrade(run_in_transaction=True)
        if migrations:
            total += 1
            print("[green]migrated[/green]")
        else:
            print("no changes")

    if total:
        print(f"[green]{total} change{'s' if total > 1 else ''} applied.[/green]")
    else:
        print("No changes found.")


@app.command()
@db_command
async def init(app: str = None):
    coloco_app = get_coloco_app()
    has_migrations = await ensure_migrations_init(coloco_app)
    if not has_migrations:
        print("[green]Database initialized.[/green]")
    else:
        print("[green]Database already initialized.[/green]")


@app.command()
@db_command
async def revert(version: str, fake: bool = False):
    # TODO: custom reversion based on app or timestamp?
    # Reversion
    raise typer.Abort("Not implemented yet")
    command = await get_command(app)
    await command.downgrade(version=version, delete=False, fake=fake)


@app.command()
@db_command
async def heads():
    command = await get_command()
    await command.heads()


@app.command()
@db_command
async def history():
    command = await get_command()
    await command.history()
