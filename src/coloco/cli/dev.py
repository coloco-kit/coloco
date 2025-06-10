from .api import _verify_app, _serve
import cyclopts
from ..config import get_coloco_config
from .node import install, _setup_dev_env
import os
from rich import print
from subprocess import Popen

app = cyclopts.App()


@app.default()
def dev(app: str | None = None, host: str = "127.0.0.1"):
    if not app:
        app = get_coloco_config().get("app") or "src.main.app"

    _verify_app(app)

    # Check Node Modules
    if not os.path.exists(os.path.join(os.getcwd(), "node_modules")):
        print("[yellow]Node modules not found, installing...[/yellow]")
        install()

    _setup_dev_env()
    node = Popen([f"npm run dev"], shell=True)
    _serve(
        app=app,
        host=host,
        port=5172,
        log_level="debug",
        mode="dev",
        reload=True,
    )
    node.terminate()
    node.wait()
