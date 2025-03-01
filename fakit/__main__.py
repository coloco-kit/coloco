import typer
from .cli.dev import dev
from .cli.api import app as api_app
from .cli.node import app as node_app

app = typer.Typer()

app.command()(dev)
app.add_typer(node_app, name="node")
app.add_typer(api_app, name="api")

if __name__ == "__main__":
    app()
