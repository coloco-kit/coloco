from .api import ColocoRoute
from contextlib import asynccontextmanager
from collections import defaultdict
from copy import copy
from functools import wraps
from .lifespan import register_lifespan
from rich import print
from tortoise.fields import Field
from type_less import replace_type_hint_map_deep
from typing import *
import datetime

CLS = TypeVar("CLS")


IMPORT_ERROR = (
    "[red]Tortoise is not installed.  "
    "Please install it with `uv add tortoise-orm`.  "
    "If you intend to use anything other than sqlite, "
    "you will need to install the appropriate database driver as well "
    "(e.g. `uv add tortoise-orm[asyncpg]` for postgres).[/red]"
)


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
            app: {
                "models": [
                    *models,
                ],
                "default_connection": "default",
            }
            for app, models in app_to_models.items()
        },
    }


async def init_tortoise(app):
    try:
        from tortoise import Tortoise
    except ImportError:
        print(IMPORT_ERROR)
        raise
    await Tortoise.init(config=app.orm_config, table_name_generator=app_class_to_table_name)
    return Tortoise.close_connections


def register_db_lifecycle(app):
    @asynccontextmanager
    async def lifecycle_connect_database(api):
        print("[green]Connecting to database...[/green]")
        close_connections = await init_tortoise(app)
        print("[green]Database ready[/green]")
        yield
        print("[yellow]Closing database connection...[/yellow]")
        await close_connections()

    # Register DB Connection
    register_lifespan(lifecycle_connect_database)


def create_model_serializers(orm_config: dict):
    try:
        from tortoise import Tortoise
        from tortoise.contrib.pydantic import pydantic_model_creator
    except ImportError:
        print(IMPORT_ERROR)
        raise

    # TODO: find out if we can init the config without initing the DB
    Tortoise.table_name_generator = app_class_to_table_name
    for label, _app in orm_config["apps"].items():
        for model in _app["models"]:
            Tortoise.init_models([model], label, _init_relations=False)
    # Initialize foreign key relations
    Tortoise._init_relations()

    # Auto-create serializers
    # TODO: configurable
    model_classes = [cls for models in Tortoise.apps.values() for cls in models.values()]
    model_to_serializer = {}
    for model_class in model_classes:
        # Wrapped with @serializable
        if getattr(model_class, "__model_serializer_create", None):
            model_to_serializer[model_class] = pydantic_model_creator(
                model_class, **model_class.__model_serializer_create
            )
        # Create a general serializer
        elif not model_class in model_to_serializer:
            model_to_serializer[model_class] = pydantic_model_creator(model_class)

        # Inject type annotations into model
        # TODO: find a better way to do this that's less dependent on Tortoise internals
        description = model_class.describe(serializable=False)
        fields = [*description["data_fields"], description["pk_field"]]
        for field in fields:
            if field["name"] not in model_class.__annotations__:
                model_class.__annotations__[field["name"]] = field["python_type"]

    return model_to_serializer


def inject_model_serializers(model_to_serializer: dict, routes: list[ColocoRoute]):
    for route in routes:
        route.func.__annotations__["return"], occurrences = replace_type_hint_map_deep(
            route.func.__annotations__["return"],
            model_to_serializer,
        )

        # Magical model adapting (when models detected)
        # TODO: find a better way to do this than wrapping every route
        # We need to async eval the serialization
        # - Middleware - can't catch pre-serialized values
        # - Pydantic - sync serialization only
        # - JSON Encoder - sync serialization only, + happens after serialization
        if occurrences:
            route.func = _wrap_model_serializer(route.func, model_to_serializer)


async def _serialize_models(obj, model_to_serializer):
    """
    Auto-runs the serializer for tortoise models
    """
    if type(obj) in model_to_serializer:
        return await model_to_serializer[type(obj)].from_tortoise_orm(obj)
    elif isinstance(obj, list):
        return [await _serialize_models(item, model_to_serializer) for item in obj]
    elif isinstance(obj, dict):
        return {k: await _serialize_models(v, model_to_serializer) for k, v in obj.items()}
    return obj


def _wrap_model_serializer(func, model_to_serializer):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await _serialize_models(await func(*args, **kwargs), model_to_serializer)

    return wrapper
