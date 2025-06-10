import cyclopts
import os
from rich import print
import shutil
import subprocess

app = cyclopts.App()


def _run_npm(command):
    # if not exists +node/package.json, raise error
    if not os.path.exists("package.json"):
        print(
            "[red]Error: package.json not found.  Please ensure you are in a coloco project directory.[/red]"
        )
        raise SystemExit(1)

    try:
        # run npm install
        subprocess.run(command, cwd=".")
    except Exception as e:
        print(f"[red]Error: {e}[/red]")
        raise SystemExit(1)


def _setup_dev_env():
    os.environ["API_HOST"] = "http://localhost:5172"


@app.command()
def install():
    """Installs node dependencies for the project"""

    _run_npm(["npm", "install"])

    print("[green]Packages installed successfully.[/green]")


@app.command()
def add(package: str):
    """Adds a node dependency to the project"""

    _run_npm(["npm", "add", "-D", package])

    print("[green]Package added successfully.[/green]")


@app.command()
def link(package: str):
    """Links a node dependency to the project"""

    _run_npm(["npm", "link", package])

    print("[green]Package linked successfully.[/green]")


@app.command()
def dev():
    """Runs the node dev server"""
    print("[green]Running node dev server...[/green]")
    _setup_dev_env()
    subprocess.run(["npm", "run", "dev"], cwd=".")


@app.command()
def build(dir: str | None = None):
    """Runs the node dev server"""
    print("[green]Building node app...[/green]")

    subprocess.run(["npm", "run", "build", *(["--", "--outDir", dir] if dir else [])], cwd=".")
