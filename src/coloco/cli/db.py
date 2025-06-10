from .api import _verify_app
from ..app import ColocoApp, get_current_app
from asyncio import run
import cyclopts
import functools
import logging
import os
from pathlib import Path
from rich import print
from tortoise import Tortoise
from tortoise.log import logger as tortoise_logger
from tortoise_pathway.migration_manager import MigrationManager
from typing import Callable, TypeVar


T = TypeVar("T")


app = cyclopts.App()


def _get_model_apps(coloco_app: ColocoApp):
    return [app for app in coloco_app.orm_config["apps"]]


def _get_coloco_app():
    _verify_app()
    return get_current_app()


def _get_app_migrations_path_func(migrations_dir: str) -> Callable[[str], Path]:
    def _get_app_migrations_path(self, app) -> Path:
        return Path(os.path.join("src", "app", app, migrations_dir))

    return _get_app_migrations_path


def db_command(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tortoise_logger.setLevel(logging.WARNING)
        run(func(*args, **kwargs))
        run(Tortoise.close_connections())

    return app.command(name=func.__name__)(wrapper)


async def get_migration_manager():
    coloco_app = _get_coloco_app()
    apps = _get_model_apps(coloco_app)
    await Tortoise.init(config=coloco_app.orm_config)

    # TODO: propose a patch for this
    MigrationManager.get_migrations_dir = _get_app_migrations_path_func(coloco_app.migrations_dir)

    manager = MigrationManager(apps, coloco_app.migrations_dir)
    await manager.initialize()

    return manager


# ----------------------------- Commands -----------------------------


@db_command
async def makemigrations(
    app: str | None = None, name: str | None = None, empty: bool = False
) -> None:
    """Create new migration(s) based on model changes."""
    manager = await get_migration_manager()

    print(f"Making migrations for {app or 'all apps'}...", end="", flush=True)

    migrations = await manager.create_migration(name, app=app, auto=True)

    if not migrations:
        print("[gray]no changes[/gray]")
        return

    print()
    for migration in migrations:
        print(f" |- [yellow]{migration.display_name()}[/yellow] @ {migration.path()}")


@db_command
async def migrate(app: str | None = None) -> None:
    """Apply migrations to the database."""
    manager = await get_migration_manager()

    pending = manager.get_pending_migrations(app=app)

    if not pending:
        print("[gray]No pending migrations.[/gray]")
        return

    s = "s" if len(pending) > 1 else ""
    print(f"Applying [cyan]{len(pending)}[/cyan] migration{s}:")

    applied = []
    async for migration in manager.apply_migrations_async(app=app):
        print(f" |- [cyan]{migration.display_name()}[/cyan]")
        applied.append(migration)

    if applied:
        print(f"[green]Successfully applied {len(applied)} migration{s}[/green]")
    else:
        print("[gray]No migrations were applied.[/gray]")


@db_command
async def rollback(app: str | None = None, migration: str | None = None) -> None:
    """Revert the most recent migration."""
    manager = await get_migration_manager()

    reverted = await manager.revert_migration(migration=migration, app=app)

    if reverted:
        print(f"Successfully reverted migration: [yellow]{reverted.display_name()}[/yellow]")
    else:
        print("[gray]No migration was reverted.[/gray]")


@db_command
async def showmigrations(app: str | None = None) -> None:
    """Show migration status."""
    manager = await get_migration_manager()

    applied = manager.get_applied_migrations(app=app)
    pending = manager.get_pending_migrations(app=app)

    print(f"Migrations for {app}:" if app else "All Migrations:")
    print("\nApplied migrations:")
    if applied:
        for migration in applied:
            print(f"  [X] {migration.display_name()}")
    else:
        print("  (none)")

    print("\nPending migrations:")
    if pending:
        for migration in pending:
            print(f"  [ ] {migration.display_name()}")
    else:
        print("  (none)")
