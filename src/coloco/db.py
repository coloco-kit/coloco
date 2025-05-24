from contextlib import asynccontextmanager
from collections import defaultdict
from rich import print


def app_class_to_table_name(cls):
    try:
        app_name = cls.__module__.split(".")[-2]
    except IndexError:
        raise ValueError(f"Could not determine app name for model {cls}")
    return f"{app_name}_{cls.__name__.lower()}"


def get_orm_config(database_url: str, model_files: list[str]):
    model_modules = [
        model_file.replace("./", "").replace("/", ".").replace(".py", "")
        for model_file in model_files
    ]
    app_to_models = defaultdict(list)
    for model_module in model_modules:
        app = model_module.lstrip("src.app.").split(".")[0]
        app_to_models[app].append(model_module)
    return {
        "connections": {"default": database_url},
        "table_name_generator": app_class_to_table_name,
        "apps": {
            **{
                app: {
                    "models": [
                        *models,
                    ],
                    "default_connection": "default",
                }
                for app, models in app_to_models.items()
            },
            **{
                "models": {
                    "models": [
                        "aerich.models",
                    ],
                    "default_connection": "default",
                }
            },
        },
    }


async def init_tortoise(app):
    try:
        from tortoise import Tortoise
    except ImportError:
        print(
            "[red]Tortoise is not installed.  "
            "Please install it with `pip install tortoise-orm`.  "
            "If you intend to use anything other than sqlite, "
            "you will need to install the appropriate database driver as well "
            "(e.g. `pip install tortoise-orm[asyncpg]` for postgres).[/red]"
        )
        raise
    await Tortoise.init(
        config=app.orm_config, table_name_generator=app_class_to_table_name
    )
    return Tortoise.close_connections


def create_lifecycle_connect_database(app):
    @asynccontextmanager
    async def lifecycle_connect_database(api):
        from .app import get_current_app

        app = get_current_app()

        print("[green]Connecting to database...[/green]")
        close_connections = await init_tortoise(app)
        print("[green]Database ready[/green]")
        yield
        print("[yellow]Closing database connection...[/yellow]")
        await close_connections()

    return lifecycle_connect_database
