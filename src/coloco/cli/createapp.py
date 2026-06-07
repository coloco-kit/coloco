import os

from .shared.logging import get_cli_logger

cli = get_cli_logger()


def createapp(name: str):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = f"{current_dir}/../templates/standard"
    install_dir = f"{os.getcwd()}/{name}"
    cli.info(f"Creating app {name}...")

    template_vars = {
        "project_name": name,
        "coloco_version": "0.4.8",
    }

    # Create directory
    os.makedirs(install_dir, exist_ok=True)

    # Copy all tpl files in folders and subfolders to install_dir under their relative paths
    for root, dirs, files in os.walk(template_dir):
        relative_path = os.path.relpath(root, template_dir)
        install_subdir = os.path.join(install_dir, relative_path)
        if not os.path.exists(install_subdir):
            os.makedirs(install_subdir)
        for file in files:
            if file.endswith("-tpl"):
                with open(os.path.join(root, file), "r") as f:
                    content = f.read()
                for key, value in template_vars.items():
                    content = content.replace(f"{{{{ {key} }}}}", value)
                with open(os.path.join(install_dir, relative_path, file[:-4]), "w") as f:
                    f.write(content)

    cli.info(f"App created in {install_dir}")

    cli.info(f"\nRun [green]coloco dev[/green] from [yellow]{name}[/yellow] to start the app.")
