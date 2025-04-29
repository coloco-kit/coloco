import tomllib
import os


def get_coloco_config():
    # Read project toml
    if not os.path.exists("pyproject.toml"):
        raise LookupError("pyproject.toml not found")
    with open("pyproject.toml", "rb") as f:
        config = tomllib.load(f)

    # Get coloco config
    coloco_config = config.get("tool", {}).get("coloco")
    if not coloco_config:
        raise LookupError(
            "coloco config not found in pyproject.toml under [tool.coloco]"
        )
    return coloco_config
