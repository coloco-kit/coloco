from .api import create_api, global_routes
from dataclasses import dataclass
from .db import (
    get_orm_config,
    inject_model_serializers,
    register_db_lifecycle,
)
from fastapi import APIRouter, FastAPI
from importlib import import_module
import os
from rich import print
from .static import bind_static
import traceback
from type_less import fill_type_hints
from typing import Literal


@dataclass
class ColocoApp:
    api: FastAPI
    name: str
    database_url: str = None
    orm_config: dict = None
    migrations_dir: str = "+migrations"


def discover_files(directory, name, is_dev=False):
    api_files = []
    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_dir():
                    # Skip directories starting with "+" and "node_modules"
                    if (
                        not entry.name.startswith("+")
                        and (not entry.name.startswith("-") or is_dev)
                        and not entry.name.startswith(".")
                        and not entry.name == "node_modules"
                        and not entry.name == "coloco"
                    ):
                        api_files.extend(discover_files(entry.path, name, is_dev))
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

    src_path = "src"

    # Discover all api.py files from root, excluding node_modules and +app
    api_files = discover_files(src_path, name="api.py", is_dev=mode == "dev")
    for api_file in api_files:
        # convert python file path to module path
        module_name = api_file.replace("./", "").replace(".py", "").replace("/", ".")
        try:
            module = import_module(module_name)
        except Exception as e:
            print(f"[red]Error importing '{api_file}': {e}[/red]")
            print(traceback.format_exc())
            continue

    # Inject type hints
    for route in global_routes:
        fill_type_hints(route.func, use_literals=True)

    # Setup Database
    # We need this first to grab the models for route type hints
    has_database = bool(database_url)
    if has_database:
        orm_config = get_orm_config(
            database_url,
            model_files=discover_files(src_path, name="models.py", is_dev=mode == "dev"),
        )
        inject_model_serializers(orm_config, global_routes)
    else:
        orm_config = None

    router = APIRouter()
    for route in global_routes:
        router.api_route(
            *route.args,
            **{
                **route.kwargs,
                **{
                    "summary": (
                        route.kwargs.get("summary", "") + f" ({route.module_name})"
                    ).strip(),
                    "methods": [route.method],
                },
            },
        )(route.func)
    api.include_router(router)

    # Production mode serves dist
    if mode == "prod":
        bind_static(api)

    CURRENT_APP = ColocoApp(api=api, name=name, database_url=database_url, orm_config=orm_config)

    if database_url:
        register_db_lifecycle(CURRENT_APP)

    return CURRENT_APP


def get_current_app() -> ColocoApp:
    if not CURRENT_APP:
        raise ValueError("Coloco app not created")
    return CURRENT_APP
