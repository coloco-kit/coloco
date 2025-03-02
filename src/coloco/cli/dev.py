from rich import print
from .api import serve
from subprocess import Popen


def dev(app: str = "main.app", host: str = "127.0.0.1"):
    node = Popen([f"npm run dev"], cwd="+node", shell=True)
    serve(
        app=app,
        host=host,
        port=5172,
        reload=True,
        log_level="debug",
    )
    node.terminate()
    node.wait()
