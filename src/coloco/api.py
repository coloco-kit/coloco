from .codegen import (
    custom_generate_unique_id,
    generate_openapi_code,
    generate_openapi_schema,
)
from contextlib import asynccontextmanager
from dataclasses import dataclass
from .exceptions import bind_exceptions
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .lifespan import execute_lifespan, register_lifespan
import logging
from os import environ
from threading import Thread
from type_less import fill_type_hints
from typing import Callable, TypeVar


logging.basicConfig(level=logging.INFO)


T = TypeVar("T")


@dataclass
class ColocoRoute:
    args: tuple
    kwargs: dict
    func: Callable
    method: str
    module_name: str


def _generate_openapi_thread(app: FastAPI):
    # TODO: diff check the schema json
    # TODO: diff check not working
    logging.info("Generating OpenAPI schema in thread...")
    generate_openapi_schema(app)
    generate_openapi_code(host=f"http://localhost:5172", diff_files=True)


@asynccontextmanager
async def generate_openapi(app: FastAPI):
    generate_api_thread = Thread(target=_generate_openapi_thread, args=(app,))
    generate_api_thread.start()
    yield
    # TODO: possibly use a process and terminate instead?
    generate_api_thread.join()


def create_api(is_dev: bool = False):
    kwargs = {
        "lifespan": execute_lifespan,
    }
    if not is_dev:
        kwargs = {
            **kwargs,
            "openapi_url": None,
            "docs_url": None,
            "redoc_url": None,
        }
    else:
        register_lifespan(generate_openapi)

    api = FastAPI(
        generate_unique_id_function=custom_generate_unique_id,
        **kwargs,
    )
    api.service = CORSMiddleware(
        app=api,
        allow_origins=[
            f"http://localhost:5173",
            "https://mysite.app",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    bind_exceptions(api, debug=is_dev)

    return api


# ========================= Global routing =========================

global_routes: list[ColocoRoute] = []


def api(func):
    # Auto-route
    return _add_global_route([f"/{func.__name__}"], {}, func, "GET")


def _add_global_route(args, kwargs, func, method: str):
    module_name = func.__module__.lstrip("src.app")

    # Prepend module name to path
    path = args[0] if args else kwargs.get("path", "")
    path = (
        # TODO: Make this configurable
        "/api/"
        # TODO: Make this read project configuration, probably need to add routes after running
        + module_name.rsplit(".", 1)[0]
        .replace(".", "/")
        .replace(".-", ".")  # Strip - from folders (for dev only)
        .lstrip("-")
        + ("" if path.startswith("/") else "/")
        + path
    )
    if args:
        args = (path, *args[1:])
    else:
        kwargs["path"] = path

    return global_routes.append(ColocoRoute(args, kwargs, func, method, module_name))


def _make_route_decorator(method: str) -> Callable[..., Callable[[T], T]]:
    def route_wrapper(*args, **kwargs) -> Callable[[T], T]:
        def handler_wrapper(func):
            return _add_global_route(args, kwargs, func, method)

        return handler_wrapper

    return route_wrapper


api.get = _make_route_decorator("GET")
api.post = _make_route_decorator("POST")
api.put = _make_route_decorator("PUT")
api.delete = _make_route_decorator("DELETE")
