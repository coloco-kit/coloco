from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from os import environ
from .codegen import (
    custom_generate_unique_id,
    generate_openapi_code,
    generate_openapi_schema,
)
from .lifespan import execute_lifespan, register_lifespan
from .static import bind_static
from .exceptions import bind_exceptions


logging.basicConfig(level=logging.INFO)

# Strip development options
IS_PRODUCTION_MODE = environ.get("ENV") == "production"


@asynccontextmanager
async def generate_openapi(app: FastAPI):
    logging.info("Generating OpenAPI schema...")
    generate_openapi_schema(app)
    generate_openapi_code(host=f"http://localhost:5172", diff_files=True)

    yield


def create_api(is_dev: bool = False):
    if not is_dev:
        kwargs = {
            "openapi_url": None,
            "docs_url": None,
            "redoc_url": None,
        }
    else:
        kwargs = {
            "lifespan": execute_lifespan,
        }
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

    # bind_static(api)
    bind_exceptions(api)

    return api
