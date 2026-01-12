import json
import os
import shutil

import typer
from gws_core.brick.brick_service import BrickService
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper

from gws_cli.ai_code.claude_service import ClaudeService
from gws_cli.ai_code.copilot_service import CopilotService


class DevEnvCliService:
    """Service for configuring development environment settings."""

    # Get the directory where the dev_env module is located
    TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template")

    CUSTOM_GWS_CORE_REFLEX_PATH = os.path.join("gws_core", "apps", "reflex", "_gws_reflex")
    OPENVSCODE_SERVER_BIN = "/home/.openvscode-server/bin/openvscode-server"

    @classmethod
    def configure_dev_env(cls, force: bool = False) -> None:
        """Configure the development environment.

        Args:
            force: If True, delete all generated files before configuring VSCode.
        """
        cls.configure_vscode(force=force)

        # Update claude config if installed
        claude_service = ClaudeService()
        claude_service.update_if_configured()

        # Update copilot config if installed
        copilot_service = CopilotService()
        copilot_service.update_if_configured()

    @classmethod
    def configure_vscode(cls, force: bool = False) -> None:
        """Configure VS Code with recommended settings, extensions, and Python paths for all bricks.

        Args:
            force: If True, delete all generated files before configuring VSCode.
        """
        typer.echo("Configuring VS Code...")

        vs_code_folder = cls.get_vs_code_setting_folder()
        notebook_template_dir = os.path.join(Settings.get_user_folder(), "notebooks", "template")

        # Delete generated files if force is True
        if force:
            typer.echo("Force option enabled. Deleting generated files...")
            if os.path.exists(vs_code_folder):
                typer.echo(f"Deleting {vs_code_folder}...")
                shutil.rmtree(vs_code_folder)
            if os.path.exists(notebook_template_dir):
                typer.echo(f"Deleting {notebook_template_dir}...")
                shutil.rmtree(notebook_template_dir)

        if not os.path.exists(vs_code_folder):
            os.mkdir(vs_code_folder)

        # Always override the extensions.json file
        extensions_dest = os.path.join(vs_code_folder, "extensions.json")
        shutil.copyfile(os.path.join(cls.TEMPLATE_DIR, "extensions.json"), extensions_dest)

        # Always override the launch.json file
        shutil.copyfile(
            os.path.join(cls.TEMPLATE_DIR, "launch.json"),
            os.path.join(vs_code_folder, "launch.json"),
        )

        # Copy the ruff.toml file
        shutil.copyfile(
            os.path.join(cls.TEMPLATE_DIR, "ruff.toml"),
            os.path.join(Settings.get_user_folder(), "ruff.toml"),
        )

        cls.config_vs_code_settings_json()
        cls.install_notebook_template()
        cls._install_vscode_extensions(extensions_dest)

        typer.echo("VS Code configured successfully!")

    @classmethod
    def get_vs_code_setting_folder(cls) -> str:
        """Get the VS Code settings folder path."""
        return os.path.join(Settings.get_user_folder(), ".vscode")

    @classmethod
    def get_vs_code_settings_file_path(cls) -> str:
        """Get the VS Code settings.json file path."""
        return os.path.join(cls.get_vs_code_setting_folder(), "settings.json")

    @classmethod
    def config_vs_code_settings_json(cls) -> None:
        """Configure the vscode settings.json file to add the bricks to the python path."""
        typer.echo("Configuring VS Code settings.json file...")
        settings_path = cls.get_vs_code_settings_file_path()

        # Load the settings file into a dict
        settings: dict
        if not os.path.exists(settings_path):
            typer.echo("Creating a new vscode settings file")
            settings = cls.generate_vs_code_settings_json(settings_path)
        else:
            typer.echo("Reading the existing vscode settings file")
            try:
                with open(settings_path, encoding="UTF-8") as file:
                    settings = json.load(file)
            except Exception as err:
                typer.echo(f"Error during parsing of the vscode settings file: {err}", err=True)
                typer.echo(
                    "Moving the existing file to settings_backup.json and creating a new one..."
                )
                shutil.move(
                    settings_path,
                    os.path.join(cls.get_vs_code_setting_folder(), "settings_backup.json"),
                )
                # Create a new settings file
                settings = cls.generate_vs_code_settings_json(settings_path)
                return

        typer.echo("Adding the bricks to the python path...")
        # Init the extra paths if not already done
        if "python.autoComplete.extraPaths" not in settings or not isinstance(
            settings["python.autoComplete.extraPaths"], list
        ):
            settings["python.autoComplete.extraPaths"] = []

        if "python.analysis.extraPaths" not in settings or not isinstance(
            settings["python.analysis.extraPaths"], list
        ):
            settings["python.analysis.extraPaths"] = []

        # Add the brick paths to the extra paths
        existing_paths: list[str] = settings["python.autoComplete.extraPaths"]

        # remove all bricks paths from existing paths
        user_folder = Settings.get_user_bricks_folder()
        system_folder = Settings.get_sys_bricks_folder()
        existing_paths = [
            path
            for path in existing_paths
            if not path.startswith(user_folder) and not path.startswith(system_folder)
        ]

        # Set all the brick src paths in the extraPaths
        brick_folders = BrickService.list_brick_directories(distinct=True)

        for brick_folder in brick_folders:
            brick_src_path = os.path.join(brick_folder.path, BrickService.SOURCE_FOLDER)
            existing_paths.append(brick_src_path)

            # Add special path for gws_core Reflex
            if brick_folder.name == Settings.get_gws_core_brick_name():
                reflex_path = os.path.join(brick_src_path, cls.CUSTOM_GWS_CORE_REFLEX_PATH)
                if os.path.exists(reflex_path):
                    existing_paths.append(reflex_path)

        settings["python.autoComplete.extraPaths"] = existing_paths
        settings["python.analysis.extraPaths"] = existing_paths

        try:
            typer.echo("Writing the vscode settings file...")
            # Write the settings file
            with open(settings_path, "w", encoding="UTF-8") as file:
                json.dump(settings, file, indent=2)
        except Exception as err:
            typer.echo(f"Error during writing the vscode settings file: {err}", err=True)
            return

    @classmethod
    def generate_vs_code_settings_json(cls, settings_path: str) -> dict:
        """Generate a new VS Code settings.json file from template."""
        # Copy the settings.json file only if it does not exist
        shutil.copyfile(os.path.join(cls.TEMPLATE_DIR, "settings.json"), settings_path)

        # Load the settings file into a dict
        with open(settings_path, encoding="UTF-8") as file:
            return json.load(file)

    @classmethod
    def install_notebook_template(cls):
        """Install notebook template to the notebooks folder."""
        typer.echo("Installing notebook template...")

        src_notebook_dir = os.path.join(cls.TEMPLATE_DIR, "notebook_template")
        destination_dir = os.path.join(Settings.get_user_folder(), "notebooks", "template")

        FileHelper.create_dir_if_not_exist(destination_dir)
        FileHelper.copy_dir_content_to_dir(src_notebook_dir, destination_dir)

    @classmethod
    def _install_vscode_extensions(cls, extension_file_path: str) -> None:
        """Install the vscode extensions if OpenVSCode server is available."""
        # Only install extensions if OpenVSCode server binary exists
        if not os.path.exists(cls.OPENVSCODE_SERVER_BIN):
            typer.echo("OpenVSCode server not found, skipping extension installation.")
            return

        typer.echo("Installing vscode extensions...")

        try:
            # Load the extensions file
            with open(extension_file_path, encoding="UTF-8") as file:
                extensions = json.load(file)

            # Install each extension
            for extension in extensions.get("recommendations", []):
                typer.echo(f"Installing extension {extension}...")
                os.system(f"{cls.OPENVSCODE_SERVER_BIN} --install-extension {extension}")

            typer.echo("Extensions installation completed.")
        except Exception as err:
            typer.echo(f"Error during extension installation: {err}", err=True)
