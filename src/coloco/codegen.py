from contextlib import contextmanager
from subprocess import run
import filecmp
import json
import logging
import os
import shutil

from fastapi import FastAPI
from fastapi.routing import APIRoute

logger = logging.getLogger("coloco.codegen")


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
        os.makedirs(target_path, exist_ok=True)  # Create target directory if it doesn't exist

        for file in files:
            source_file = os.path.join(root, file)
            target_file = os.path.join(target_path, file)

            if not os.path.exists(target_file) or not filecmp.cmp(source_file, target_file):
                shutil.copy2(source_file, target_file)


def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.name}"


def generate_openapi_schema(app: FastAPI, path="/tmp/openapi.json"):
    with open(path, "w") as f:
        json.dump(app.openapi(), f)


@contextmanager
def ensure_openapi_ts_config(config_path="./openapi-ts.config.ts", output_path="./api/app"):
    """
    Ensures an openapi-ts config file is present, otherwise temporarily generates one
    """
    generated = False
    try:
        if not os.path.exists(config_path):
            with open(config_path, "w") as f:
                generated = True
                f.write(
                    f"""
                        import {{ defaultPlugins }} from '@hey-api/openapi-ts';
                        import {{ codegenConfig }} from '@coloco/api-client-svelte';

                        export default {{
                            plugins: [
                                ...defaultPlugins,
                                '@hey-api/client-fetch',
                                codegenConfig({{ name: 'coloco-codegen', outputPath: '{output_path}' }}),
                            ],
                        }};
                    """
                )
        yield
    finally:
        if generated:
            os.remove(config_path)


def generate_openapi_code(
    host,
    spec_path="/tmp/openapi.json",
    output_dir="./src/app/.generated/client",
    config_path="./openapi-ts.config.ts",
    diff_files=False,
):
    temp_dir = "/tmp/backend_api"
    output_path = os.path.join(os.getcwd(), output_dir)

    with ensure_openapi_ts_config(config_path):
        result = run(
            f"npx openapi-ts "
            f"--base {host} "
            f"--file {config_path} "
            f"--input {spec_path} "
            f"--output {temp_dir if diff_files else output_path} ".split(),
            cwd=os.getcwd(),
            capture_output=True,
        )

        output = result.stdout.decode("utf-8")
        error = result.stderr.decode("utf-8")

        logger.info(output)
        if result.returncode != 0:
            logger.error(f"Failed to generate OpenAPI code: {error}")
            raise RuntimeError(f"Failed to generate OpenAPI code: {error}")

        if diff_files:
            compare_and_copy(temp_dir, output_dir)
