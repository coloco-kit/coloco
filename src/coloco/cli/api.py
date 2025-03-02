from importlib import import_module
import typer
from rich import print
import uvicorn
from ..app import ColocoApp


app = typer.Typer()


@app.command()
def serve(
    app: str = "main.app",
    host: str = "127.0.0.1",
    port: int = 80,
    log_level: str = "info",
    reload=False,
):
    if not "." in app:
        print(
            "[red]App should be the name of a variable in a python file, example: main.py -> api = main.api[/red]"
        )
        raise typer.Abort()

    module_name, var_name = app.rsplit(".", 1)
    try:
        module = import_module(module_name)
    except ImportError:
        print(f"[red]Module or python file {module_name} not found[/red]")
        raise typer.Abort()

    if not hasattr(module, var_name):
        print(f"[red]Variable {var_name} not found in module {module_name}[/red]")
        raise typer.Abort()

    var = getattr(module, var_name)

    if not isinstance(var, ColocoApp):
        print(f"[red]{var_name} is not a ColocoApp.  Please use create_app[/red]")
        raise typer.Abort()

    uvicorn.run(
        f"{module_name}:{var_name}.api.service",
        host=host,
        port=port,
        reload=reload,
        log_level=log_level,
    )
