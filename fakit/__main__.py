import typer
from .cli.dev import dev
from .cli.node import app as node_app

app = typer.Typer()

app.command()(dev)
app.add_typer(node_app, name="node")


if __name__ == "__main__":
    app()
