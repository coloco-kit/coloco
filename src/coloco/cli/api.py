from importlib import import_module
from typing import Literal
import os
import sys

import cyclopts
import uvicorn

from ..app import ColocoApp
from ..codegen import generate_openapi_code, generate_openapi_schema
from .shared.logging import get_cli_logger

app = cyclopts.App()

DEFAULT_APP = "src.main.app"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 80
DEFAULT_LOG_LEVEL = "info"
DEFAULT_MODE = "prod"
DEFAULT_RELOAD = False


cli = get_cli_logger()


def _verify_app(app: str = DEFAULT_APP) -> ColocoApp:
    if "." not in app:
        cli.error(
            "App should be the name of a variable in a python file, example: main.py -> api = main.api"
        )
        raise SystemExit(1)

    module_name, var_name = app.rsplit(".", 1)
    try:
        # Needed for when running the binary
        sys.path.append(os.getcwd())
        module = import_module(module_name)
    except ModuleNotFoundError:
        cli.error(f"Module or python file {module_name} not found")
        raise SystemExit(1)

    if not hasattr(module, var_name):
        cli.error(f"Variable {var_name} not found in module {module_name}")
        raise SystemExit(1)

    var = getattr(module, var_name)

    if not isinstance(var, ColocoApp):
        cli.error(f"{var_name} is not a ColocoApp.  Please use create_app")
        raise SystemExit(1)

    return var


def _verify_is_packaged():
    dist_dir = os.path.join(os.getcwd(), "dist")
    app_dir = os.path.join(dist_dir, "app")

    # Verify dist dir exists
    if not os.path.exists(dist_dir):
        cli.error(
            f"Dist dir {dist_dir} does not exist.  Run [green]coloco build[/green] to package the app."
        )
        raise SystemExit(1)
    if not os.path.exists(app_dir):
        cli.error(
            f"App is missing from package directory {app_dir}.  Run [green]coloco build[/green] to package the app."
        )
        raise SystemExit(1)


def _uvicorn_app_target(app: str) -> str:
    module_name, var_name = app.rsplit(".", 1)
    return f"{module_name}:{var_name}.api.service"


def _uvicorn_command(
    app: str = DEFAULT_APP,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    log_level: str = DEFAULT_LOG_LEVEL,
    reload: bool = DEFAULT_RELOAD,
) -> list[str]:
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        _uvicorn_app_target(app),
        "--host",
        host,
        "--port",
        str(port),
        "--log-level",
        log_level,
    ]
    if reload:
        command.append("--reload")
    return command


def _prepare_server(
    app: str = DEFAULT_APP,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    log_level: str = DEFAULT_LOG_LEVEL,
    mode: Literal["dev", "prod"] = DEFAULT_MODE,
    reload=DEFAULT_RELOAD,
):
    os.environ["COLOCO_MODE"] = mode

    config = uvicorn.Config(
        _uvicorn_app_target(app),
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )

    # Add the current directory to the Python path
    sys.path.insert(0, os.getcwd())

    return uvicorn.Server(config=config)


@app.command()
def serve(
    app: str = DEFAULT_APP,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    log_level: str = DEFAULT_LOG_LEVEL,
    mode: Literal["dev", "prod"] = DEFAULT_MODE,
    reload: bool = DEFAULT_RELOAD,
):
    _verify_app(app)
    if mode == "prod":
        _verify_is_packaged()
    server = _prepare_server(
        app=app, host=host, port=port, log_level=log_level, mode=mode, reload=reload
    )
    server.run()


@app.command()
def codegen(
    app: str = "main.app",
):
    coloco_app = _verify_app(app)
    cli.info("Generating OpenAPI code...")
    generate_openapi_schema(coloco_app.api)
    generate_openapi_code(host="http://localhost:5172")
    cli.info("[green]OpenAPI code generated successfully.[/green]")
