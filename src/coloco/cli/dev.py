import os

from rich import print
import cyclopts

from ..config import get_coloco_config
from .api import _uvicorn_command, _verify_app
from .node import _setup_dev_env, install
from .shared.logging import get_cli_logger
from .shared.muiltiprocess import Process, run_multiprocesses

app = cyclopts.App()

cli = get_cli_logger()


@app.default()
def dev(app: str | None = None, host: str = "127.0.0.1", port: int = 5172):
    if not app:
        app = get_coloco_config().get("app") or "src.main.app"

    _verify_app(app)

    # Check Node Modules
    if not os.path.exists(os.path.join(os.getcwd(), "node_modules")):
        cli.warning("Node modules not found, installing...")
        install()

    _setup_dev_env()
    os.environ["COLOCO_MODE"] = "dev"

    run_multiprocesses(
        [
            Process(
                title="Backend",
                command=_uvicorn_command(
                    app=app,
                    host=host,
                    port=port,
                    log_level="debug",
                    reload=True,
                ),
            ),
            Process(title="Frontend", command=["npm", "run", "dev"]),
        ]
    )
