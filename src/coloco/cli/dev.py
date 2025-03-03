from .api import _verify_app, _serve
from .node import install
import os
from rich import print
from subprocess import Popen


def dev(app: str = "main.app", host: str = "127.0.0.1"):
    _verify_app(app)

    # Check Node Modules
    if not os.path.exists(os.path.join(os.getcwd(), "node_modules")):
        print("[yellow]Node modules not found, installing...[/yellow]")
        install()
    
    node = Popen([f"npm run dev"], cwd="+node", shell=True)
    _serve(
        app=app,
        host=host,
        port=5172,
        reload=True,
        log_level="debug",
    )
    node.terminate()
    node.wait()
