from fastapi import FastAPI
from fastapi.routing import APIRoute
import json
from subprocess import run

import os
import shutil
import filecmp


def compare_and_copy(source_dir, target_dir):
    """
    Compares files in two directories and copies files from source to target if they differ, creating target directories if needed.

    Args:
        source_dir (str): Path to the source directory.
        target_dir (str): Path to the target directory.
    """
    for root, _, files in os.walk(source_dir):
        rel_path = os.path.relpath(root, source_dir)  # Get relative path from source
        target_path = os.path.join(target_dir, rel_path)
        os.makedirs(
            target_path, exist_ok=True
        )  # Create target directory if it doesn't exist

        for file in files:
            source_file = os.path.join(root, file)
            target_file = os.path.join(target_path, file)

            if not os.path.exists(target_file) or not filecmp.cmp(
                source_file, target_file
            ):
                shutil.copy2(source_file, target_file)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.name}"


def generate_openapi_schema(app: FastAPI, path="/tmp/openapi.json"):
    with open(path, "w") as f:
        json.dump(app.openapi(), f)


def generate_openapi_code(
    host,
    spec_path="/tmp/openapi.json",
    output_dir="./src/app/.generated/client",
    diff_files=False,
):
    temp_dir = "/tmp/backend_api"
    output_path = os.path.join(os.getcwd(), output_dir)

    run(
        f"npx openapi-ts "
        f"--base {host} "
        f"--input {spec_path} "
        f"--output {temp_dir if diff_files else output_path} ".split(),
        cwd=os.getcwd(),
    )
    if diff_files:
        compare_and_copy(temp_dir, output_dir)
