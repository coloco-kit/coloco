from .api import _serve
from ..config import get_coloco_config


def serve(
    app: str | None = None,
    port: int = 80,
    host: str = "0.0.0.0",
    log_level: str = "info",
):
    if not app:
        app = get_coloco_config().get("app") or "src.main.app"

    return _serve(app=app, host=host, port=port, log_level=log_level, mode="prod")
