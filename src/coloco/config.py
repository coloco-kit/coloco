import os
import tomllib


def get_pyproject_config(path: str = "pyproject.toml"):
    # Read project toml
    if not os.path.exists(path):
        raise LookupError(f"{path} not found")
    with open(path, "rb") as f:
        config = tomllib.load(f)
    return config


def get_coloco_config():
    # Read project toml
    config = get_pyproject_config()

    # Get coloco config
    coloco_config = config.get("tool", {}).get("coloco")
    if not coloco_config:
        raise LookupError(
            "coloco config not found in pyproject.toml under [tool.coloco]"
        )
    return coloco_config
