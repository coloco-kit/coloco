from contextlib import asynccontextmanager
from rich import print

def get_orm_config(database_url: str, model_files: list[str]):
    return {
        "connections": {
            "default": database_url
        },
        "apps": {
            "models": {
                "models": [
                    *[model_file.replace("./", "").replace("/", ".").replace(".py", "") for model_file in model_files],
                    "aerich.models",
                ],
                "default_connection": "default",
            },
        },
    }

@asynccontextmanager
async def lifecycle_connect_database(api):
    from .app import get_current_app
    app = get_current_app()

    try:
        from tortoise import Tortoise
    except ImportError:
        print("[red]Tortoise is not installed.  "
              "Please install it with `pip install tortoise-orm`.  "
              "If you intend to use anything other than sqlite, "
              "you will need to install the appropriate database driver as well "
              "(e.g. `pip install tortoise-orm[asyncpg]` for postgres).[/red]")
        raise
    print("[green]Connecting to database...[/green]")
    await Tortoise.init(config=app.orm_config)
    print("[green]Database ready[/green]")
    yield
    print("[yellow]Closing database connection...[/yellow]")
    await Tortoise.close_connections()