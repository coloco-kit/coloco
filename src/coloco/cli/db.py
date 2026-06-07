from asyncio import run
from pathlib import Path
from typing import Callable, TypeVar
import functools
import logging
import os

from tortoise import Tortoise
from tortoise.cli import cli as tortoise_cli
from tortoise.log import logger as tortoise_logger
import cyclopts

from ..app import ColocoApp, get_current_app
from .api import DEFAULT_APP, _verify_app
from .shared.logging import get_cli_logger

T = TypeVar("T")


app = cyclopts.App()

cli = get_cli_logger()


def _get_coloco_app(app: str | None = DEFAULT_APP):
    _verify_app(app)
    return get_current_app()


def db_command(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        tortoise_logger.setLevel(logging.WARNING)
        run(func(*args, **kwargs))
        try:
            run(Tortoise.close_connections())
        except RuntimeError:
            # TODO: figure out why the event loop is closed already when using postgres
            pass

    return app.command(name=func.__name__)(wrapper)


async def get_tortoise(coloco_app: ColocoApp):
    return await Tortoise.init(config=coloco_app.orm_config)


def prep_tortoise_cli(coloco_app: ColocoApp):
    tortoise_cli._load_config = lambda ctx: coloco_app.orm_config
    ctx = tortoise_cli.CLIContext(config=coloco_app.orm_config, config_file=None)
    app_labels = coloco_app.orm_config.apps.keys()
    return ctx, app_labels


# ----------------------------- Commands -----------------------------


@db_command
async def makemigrations(
    app: str | None = DEFAULT_APP,
    app_label: str | None = None,
    name: str | None = None,
    empty: bool = False,
) -> None:
    """Create new migration(s) based on model changes."""
    coloco_app = _get_coloco_app(app=app)
    await get_tortoise(coloco_app)

    ctx, app_labels = prep_tortoise_cli(coloco_app)
    return await tortoise_cli.makemigrations(ctx, app_labels, empty, name)


@db_command
async def migrate(
    app: str | None = DEFAULT_APP,
    app_label: str | None = None,
    dry_run: bool = False,
    fake: bool = False,
) -> None:
    """Apply migrations to the database."""
    coloco_app = _get_coloco_app(app=app)
    await get_tortoise(coloco_app)

    ctx, _ = prep_tortoise_cli(coloco_app)
    return await tortoise_cli.migrate(
        ctx, migration=None, app_label=app_label, dry_run=dry_run, fake=fake
    )


@db_command
async def rollback(
    app: str | None = DEFAULT_APP,
    app_label: str | None = None,
    migration: str | None = None,
    fake: bool = False,
    dry_run: bool = False,
) -> None:
    """Revert the most recent migration."""
    coloco_app = _get_coloco_app(app=app)
    await get_tortoise(coloco_app)

    ctx, _ = prep_tortoise_cli(coloco_app)
    return await tortoise_cli.downgrade(
        ctx, migration=migration, app_label=app_label, fake=fake, dry_run=dry_run
    )


@db_command
async def heads(app: str | None = DEFAULT_APP) -> None:
    coloco_app = _get_coloco_app(app=app)
    await get_tortoise(coloco_app)

    ctx, app_labels = prep_tortoise_cli(coloco_app)
    return await tortoise_cli.heads(ctx, app_labels)


@db_command
async def history(app: str | None = DEFAULT_APP) -> None:
    coloco_app = _get_coloco_app(app=app)
    await get_tortoise(coloco_app)

    ctx, app_labels = prep_tortoise_cli(coloco_app)
    return await tortoise_cli.history(ctx, app_labels)
