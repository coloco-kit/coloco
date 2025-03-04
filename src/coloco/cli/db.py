from aerich import Command
from .api import _verify_app
from ..app import ColocoApp, get_current_app
from asyncio import run
import functools
import os
from rich import print
from tortoise import Tortoise
import typer

app = typer.Typer()

def get_app():
    _verify_app()
    return get_current_app()

async def get_command(app: ColocoApp = None, init: bool = True):
    app = app or get_app()
    command = Command(
        tortoise_config=app.orm_config,
        app="models",
        location=app.migrations_dir,
    )
    if init:
        await command.init()
    return command

def migrations_dir_exists(migrations_dir: str):
    migrations_dir = os.path.join(migrations_dir, "models")
    return os.path.exists(migrations_dir)

def ensure_migrations_dir(migrations_dir: str):
    if not migrations_dir_exists(migrations_dir):
        print("[red]Please run `coloco db init` first to initialize the database.[/red]")
        raise typer.Exit(code=1)

def db_command(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        run(func(*args, **kwargs))
        run(Tortoise.close_connections())
    return wrapper

@app.command()
@db_command
async def makemigrations():
    app = get_app()
    ensure_migrations_dir(app.migrations_dir)
    command = await get_command(app)
    migrations = await command.migrate(name="update", empty=False)
    if migrations:
        print("[green]Migrations created successfully.[/green]")
    else:
        print("[gray]No database changes detected.[/gray]")

@app.command()
@db_command
async def migrate():
    app = get_app()
    ensure_migrations_dir(app.migrations_dir)
    command = await get_command(app)
    migrations = await command.upgrade(run_in_transaction=True)
    if migrations:
        print("[green]Database migrated successfully.[/green]")
    else:
        print("[gray]No database changes detected.[/gray]")

@app.command()
@db_command
async def init():
    app = get_app()
    if migrations_dir_exists(app.migrations_dir):
        print("[red]Migrations directory already exists.  You may want to run `coloco db migrate` instead.[/red]")
        raise typer.Exit(code=1)
    command = await get_command(app, init=False)
    await command.init_db(safe=True)
    print("[green]Database initialized successfully.[/green]")

@app.command()
@db_command
async def revert(version: str, fake: bool = False):
    app = get_app()
    ensure_migrations_dir(app.migrations_dir)
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


