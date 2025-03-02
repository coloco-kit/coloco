from .api import create_api, global_router
from dataclasses import dataclass
from fastapi import FastAPI
from importlib import import_module
import os
from rich import print


@dataclass
class ColocoApp:
    api: FastAPI
    name: str


import os


def find_api_files(directory):
    api_files = []
    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                if entry.is_dir():
                    # Skip directories starting with "+" and "node_modules"
                    if (
                        not entry.name.startswith("+")
                        and not entry.name == "node_modules"
                        and not entry.name == "coloco"
                    ):
                        api_files.extend(find_api_files(entry.path))
                elif entry.is_file() and entry.name == "api.py":
                    api_files.append(entry.path)
    except (PermissionError, FileNotFoundError) as e:
        print(f"Error accessing {directory}: {e}")
    return api_files


def create_app(name: str):
    api = create_api(is_dev=True)

    # Discover all api.py files from root, excluding node_modules and +app
    api_files = find_api_files(".")
    for api_file in api_files:
        # convert python file path to module path
        module_name = api_file.replace("./", "").replace(".py", "").replace("/", ".")
        try:
            module = import_module(module_name)
        except Exception as e:
            print(f"[red]Error importing '{api_file}': {e}[/red]")
            continue
        # if not hasattr(module, "router"):
        #     print(f"[red]Module '{api_file}' has no router[/red]")
        #     continue
        # api.include_router(module.router)

    api.include_router(global_router)

    return ColocoApp(api=api, name=name)
