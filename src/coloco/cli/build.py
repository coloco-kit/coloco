from rich import print
from .api import _verify_app, codegen
from .node import build as build_node
import os


def build(
    app: str = "main.app",
):
    _verify_app(app)
    dist_dir = f"{os.getcwd()}/dist"
    print(f"Packaging {app}...")

    # Codegen API
    codegen(app)
    # Build node app
    build_node(dir=dist_dir)

    print(
        f"App packaged into {dist_dir}.\n"
        f"Run [green]coloco serve[/green] to start the app in production mode."
    )
