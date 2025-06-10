from .api import _verify_app, codegen
from ..config import get_coloco_config
from .node import build as build_node
import os
from pathlib import Path
from rich import print
import shutil


def build(
    app: str | None = None,
):
    if not app:
        app = get_coloco_config().get("app") or "src.main.app"

    _verify_app(app)

    cwd = Path(os.getcwd())
    source_dir = cwd / "src"
    dist_dir = cwd / "dist"
    api_dir = dist_dir / "src"
    frontend_dir = dist_dir / "static"

    print(f"Clearing {dist_dir}...")
    shutil.rmtree(dist_dir, ignore_errors=True)

    # # Codegen API
    codegen(app)

    # # Build node app
    print(f"Packaging app...")
    build_node(dir=frontend_dir)

    print(f"Adding source files...")

    api_dir.mkdir(parents=True, exist_ok=True)

    # Collect backend files
    package_api_files = get_coloco_config().get("package_api_files") or ["*.py"]
    for glob_pattern in package_api_files:
        # If glob_pattern starts with /, assume non-recursive
        files = (
            source_dir.glob(glob_pattern[1:])
            if glob_pattern.startswith("/")
            else source_dir.rglob(glob_pattern)
        )
        for file in files:
            # Skip dev files
            if "/-" in str(file):
                continue

            destination = api_dir / file.relative_to(source_dir)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(file, destination)
            print(f" |- {file.relative_to(cwd)}")

    print(f"Adding project files...")
    shutil.copy(cwd / "pyproject.toml", dist_dir / "pyproject.toml")
    shutil.copy(cwd / "uv.lock", dist_dir / "uv.lock")

    print(
        f"App packaged into {dist_dir}.\n"
        f"From the [yellow]{dist_dir}[/yellow] directory:\n"
        f"  Run [green]uv sync --frozen[/green] to install dependencies.\n"
        f"  Run [green]coloco serve[/green] to start the app in production mode.\n"
    )
