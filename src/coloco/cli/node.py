import typer
import os
from rich import print
import shutil
import subprocess

app = typer.Typer()


def _run_npm(command):
    # if not exists +node/package.json, raise error
    if not os.path.exists("+node/package.json"):
        print(
            "[red]Error: +node/package.json not found.  Please ensure you are in a coloco project directory.[/red]"
        )
        raise typer.Abort()

    # copy +node/package.json to /package.json
    shutil.copyfile("+node/package.json", "package.json")
    if os.path.exists("+node/package-lock.json"):
        shutil.copyfile("+node/package-lock.json", "package-lock.json")

    try:
        # run npm install
        subprocess.run(command, cwd=".")

        # move package.json and package-lock.json back to +node
        shutil.move("package.json", "+node/package.json")
        shutil.move("package-lock.json", "+node/package-lock.json")
    except Exception as e:
        print(f"[red]Error: {e}[/red]")
        try:
            os.remove("package.json")
            os.remove("package-lock.json")
        except Exception:
            pass
        raise typer.Abort()


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
    subprocess.run(["npm", "run", "dev"], cwd="+node")
