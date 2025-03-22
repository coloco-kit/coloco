import typer
from .cli.dev import dev
from .cli.api import app as api_app
from .cli.node import app as node_app
from .cli.createapp import createapp
from .cli.build import build
from .cli.serve import serve

app = typer.Typer()

app.command()(dev)
app.add_typer(node_app, name="node")
app.add_typer(api_app, name="api")
app.command()(build)
app.command()(createapp)
app.command()(serve)

# Add DB if tortoise/aerich are installed
try:
    from .cli.db import app as db_app

    app.add_typer(db_app, name="db")
except ImportError:
    pass

if __name__ == "__main__":
    app()
