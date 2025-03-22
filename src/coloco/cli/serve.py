from rich import print
from .api import _serve
import os
import typer
import uvicorn


def serve(
    app: str = "main.app",
    port: int = 80,
    host: str = "0.0.0.0",
    log_level: str = "info",
):
    return _serve(app=app, host=host, port=port, log_level=log_level, mode="prod")
