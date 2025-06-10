from ..app import ColocoApp
from ..codegen import generate_openapi_schema, generate_openapi_code
import cyclopts
from importlib import import_module
import os
from rich import print
import sys
from typing import Literal
import uvicorn


app = cyclopts.App()


def _verify_app(app: str = "src.main.app") -> ColocoApp:
    if not "." in app:
        print(
            "[red]App should be the name of a variable in a python file, example: main.py -> api = main.api[/red]"
        )
        raise SystemExit(1)

    module_name, var_name = app.rsplit(".", 1)
    try:
        # Needed for when running the binary
        sys.path.append(os.getcwd())
        module = import_module(module_name)
    except ModuleNotFoundError:
        print(f"[red]Module or python file {module_name} not found[/red]")
        raise SystemExit(1)

    if not hasattr(module, var_name):
        print(f"[red]Variable {var_name} not found in module {module_name}[/red]")
        raise SystemExit(1)

    var = getattr(module, var_name)

    if not isinstance(var, ColocoApp):
        print(f"[red]{var_name} is not a ColocoApp.  Please use create_app[/red]")
        raise SystemExit(1)

    return var


def _verify_is_packaged():
    dist_dir = os.path.join(os.getcwd(), "dist")
    app_dir = os.path.join(dist_dir, "app")

    # Verify dist dir exists
    if not os.path.exists(dist_dir):
        print(
            f"[red]Dist dir {dist_dir} does not exist.  Run [green]coloco build[/green] to package the app.[/red]"
        )
        raise SystemExit(1)
    if not os.path.exists(app_dir):
        print(
            f"[red]App is missing from package directory {app_dir}.  Run [green]coloco build[/green] to package the app.[/red]"
        )
        raise SystemExit(1)


def _serve(
    app: str = "main.app",
    host: str = "127.0.0.1",
    port: int = 80,
    log_level: str = "info",
    mode: Literal["dev", "prod"] = "prod",
    reload=False,
):
    module_name, var_name = app.rsplit(".", 1)
    os.environ["COLOCO_MODE"] = mode
    uvicorn.run(
        f"{module_name}:{var_name}.api.service",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )


@app.command()
def serve(
    app: str = "main.app",
    host: str = "127.0.0.1",
    port: int = 80,
    log_level: str = "info",
    mode="prod",
    reload: bool = False,
):
    _verify_app(app)
    if mode == "prod":
        _verify_is_packaged()
    _serve(app=app, host=host, port=port, log_level=log_level, mode=mode, reload=reload)


@app.command()
def codegen(
    app: str = "main.app",
):
    coloco_app = _verify_app(app)
    print("Generating OpenAPI code...")
    generate_openapi_schema(coloco_app.api)
    generate_openapi_code(host="http://localhost:5172")
    print("[green]OpenAPI code generated successfully.[/green]")
