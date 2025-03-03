from rich import print
from .node import install
import os


def createapp(name: str):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    template_dir = f"{current_dir}/../templates/standard"
    install_dir = f"{os.getcwd()}/{name}"
    print(f"Creating app {name}...")

    template_vars = {
        "project_name": name,
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
                with open(
                    os.path.join(install_dir, relative_path, file[:-4]), "w"
                ) as f:
                    f.write(content)

    print(f"App created in {install_dir}")

    print(f"\nRun [green]coloco dev[/green] from [yellow]{name}[/yellow] to start the app.")
