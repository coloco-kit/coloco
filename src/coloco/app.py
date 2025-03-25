from .api import create_api, global_router
from dataclasses import dataclass
from .db import get_orm_config, lifecycle_connect_database
from fastapi import FastAPI
from importlib import import_module
from .lifespan import register_lifespan
import os
from rich import print
from .static import bind_static
import traceback
from typing import Literal


@dataclass
class ColocoApp:
    api: FastAPI
    name: str
    database_url: str = None
    orm_config: dict = None
    migrations_dir: str = "./+migrations"


def discover_files(directory, name):
    api_files = []
    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_dir():
                    # Skip directories starting with "+" and "node_modules"
                    if (
                        not entry.name.startswith("+")
                        and not entry.name.startswith("-")
                        and not entry.name.startswith(".")
                        and not entry.name == "node_modules"
                        and not entry.name == "coloco"
                    ):
                        api_files.extend(discover_files(entry.path, name))
                elif entry.is_file() and entry.name == name:
                    api_files.append(entry.path)
    except (PermissionError, FileNotFoundError) as e:
        print(f"Error accessing {directory}: {e}")
    return api_files


CURRENT_APP = None


def create_app(name: str, database_url: str = None) -> ColocoApp:
    global CURRENT_APP
    if CURRENT_APP:
        raise ValueError("Coloco app already created")

    mode: Literal["dev", "prod"] = os.environ.get("COLOCO_MODE", "dev")
    api = create_api(is_dev=mode == "dev")

    # Discover all api.py files from root, excluding node_modules and +app
    api_files = discover_files(".", name="api.py")
    for api_file in api_files:
        # convert python file path to module path
        module_name = api_file.replace("./", "").replace(".py", "").replace("/", ".")
        try:
            module = import_module(module_name)
        except Exception as e:
            print(f"[red]Error importing '{api_file}': {e}[/red]")
            print(traceback.format_exc())
            continue

    api.include_router(global_router)

    # Production mode serves dist
    if mode == "prod":
        bind_static(api)

    # Setup Database
    if database_url:
        orm_config = get_orm_config(
            database_url, model_files=discover_files(".", name="models.py")
        )
        register_lifespan(lifecycle_connect_database)
    else:
        orm_config = None

    CURRENT_APP = ColocoApp(
        api=api, name=name, database_url=database_url, orm_config=orm_config
    )
    return CURRENT_APP


def get_current_app() -> ColocoApp:
    if not CURRENT_APP:
        raise ValueError("Coloco app not created")
    return CURRENT_APP
