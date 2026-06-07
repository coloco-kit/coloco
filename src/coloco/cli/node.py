import os
import subprocess

import cyclopts

from .shared.logging import get_cli_logger

app = cyclopts.App()

cli = get_cli_logger()


def _run_npm(command):
    # if not exists +node/package.json, raise error
    if not os.path.exists("package.json"):
        cli.error(
            "Error: package.json not found.  Please ensure you are in a coloco project directory."
        )
        raise SystemExit(1)

    try:
        # run npm install
        subprocess.run(command, cwd=".")
    except Exception as e:
        cli.error(f"Error: {e}")
        raise SystemExit(1)


def _setup_dev_env(port: int = 5172):
    os.environ["VITE_API_HOST"] = f"http://localhost:{port}"


@app.command()
def install():
    """Installs node dependencies for the project"""

    _run_npm(["npm", "install"])

    cli.info("[green]Packages installed successfully.[/green]")


@app.command()
def add(package: str):
    """Adds a node dependency to the project"""

    _run_npm(["npm", "add", "-D", package])

    cli.info("[green]Package added successfully.[/green]")


@app.command()
def link(package: str):
    """Links a node dependency to the project"""

    _run_npm(["npm", "link", package])

    cli.info("[green]Package linked successfully.[/green]")


@app.command()
def dev():
    """Runs the node dev server"""
    cli.info("[green]Running node dev server...[/green]")
    _setup_dev_env()
    subprocess.run(["npm", "run", "dev"], cwd=".")


@app.command()
def build(dir: str | None = None):
    """Runs the node dev server"""
    cli.info("[green]Building node app...[/green]")

    subprocess.run(["npm", "run", "build", *(["--", "--outDir", dir] if dir else [])], cwd=".")
