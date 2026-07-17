import json
import os
import shutil
import sys

import typer
from gws_core.brick.brick_service import BrickService
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper

from gws_cli.ai_code.claude_service import ClaudeService
from gws_cli.ai_code.copilot_service import CopilotService
from gws_cli.utils.brick_configure_service import BrickConfigureService


class DevEnvCliService:
    """Service for configuring development environment settings."""

    # Get the directory where the dev_env module is located
    TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "template")

    CUSTOM_GWS_CORE_STREAMLIT_PATH = os.path.join("gws_core", "apps", "streamlit", "_gws_streamlit")
    CUSTOM_GWS_CORE_REFLEX_PATH = os.path.join("gws_core", "apps", "reflex", "_gws_reflex")
    OPENVSCODE_SERVER_BIN = "/home/.openvscode-server/bin/openvscode-server"

    # Folders that are never worth indexing, watching or showing. Workspace-relative
    # entries (data, other-bricks) match the fixed user folder layout; the rest are
    # build output / caches that can appear under any brick. ".states" and ".web" are
    # per-app Reflex caches (see ReflexApp.CACHE_FOLDER_NAMES).
    NOISE_FOLDER_NAMES = [
        "**/node_modules",
        "**/.venv",
        "**/__pycache__",
        "**/.pytest_cache",
        "**/.ruff_cache",
        "**/.mypy_cache",
        "**/.ipynb_checkpoints",
        "**/dist",
        "**/build",
        "**/.next",
        "**/.web",
        "**/.states",
        "data",
        "other-bricks",
    ]

    # Watching a large tree exhausts the kernel's inotify handles (a frequent cause
    # of editor crashes on WSL2), so the watcher drops the noise folders plus the
    # heavy git subtrees. .git itself stays watched: VSCode reads HEAD/index/refs to
    # keep the source control view in sync.
    WATCHER_EXCLUDE_EXTRA = [
        "**/.git/objects",
        "**/.git/subtree-cache",
    ]

    # Keys that pyright owns via pyrightconfig.json. Pylance ignores them in
    # settings.json and warns when they are set, so the CLI removes them.
    PYRIGHT_OWNED_SETTINGS_KEYS = [
        "python.analysis.extraPaths",
        "python.analysis.exclude",
        "python.analysis.typeCheckingMode",
    ]

    @classmethod
    def configure_dev_env(cls, force: bool = False, configure_bricks: bool = False) -> None:
        """Configure the development environment.

        Args:
            force: If True, delete all generated files before configuring VSCode.
            configure_bricks: If True, configure user bricks with AI code instruction files.
        """
        cls.configure_vscode(force=force)

        # Configure user bricks with AI code instruction files if requested
        if configure_bricks:
            cls.configure_bricks(force=force)

        # Update claude config if installed
        claude_service = ClaudeService()
        claude_service.update_if_configured()

        # Update copilot config if installed
        copilot_service = CopilotService()
        copilot_service.update_if_configured()

    @classmethod
    def configure_bricks(cls, force: bool = False) -> None:
        """Configure user bricks with AI code instruction files.

        Only configures bricks in the user folder, not system bricks.

        Args:
            force: If True, overwrite existing generated files.
        """
        typer.echo("Configuring user bricks with AI code instruction files...")

        brick_folders = BrickService.list_brick_directories(distinct=True)

        for brick_folder in brick_folders:
            if brick_folder.folder != "user":
                continue
            typer.echo(f"Configuring brick: {brick_folder.name}...")
            BrickConfigureService.configure_brick(brick_folder.path, force=force)

        typer.echo("All user bricks configured successfully!")

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
            # Delete pytest config files + the pyright config
            user_folder = Settings.get_user_folder()
            for generated_file in ["conftest.py", "pyproject.toml", "pyrightconfig.json"]:
                generated_file_path = os.path.join(user_folder, generated_file)
                if os.path.exists(generated_file_path):
                    typer.echo(f"Deleting {generated_file_path}...")
                    os.remove(generated_file_path)

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
        cls.config_pyright_config_json()
        cls.install_notebook_template()
        cls.install_pytest_config()
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

        typer.echo("Adding the bricks to the python path...")
        # Init the extra paths if not already done
        if "python.autoComplete.extraPaths" not in settings or not isinstance(
            settings["python.autoComplete.extraPaths"], list
        ):
            settings["python.autoComplete.extraPaths"] = []

        # Remove all bricks paths from existing paths, then re-add the current
        # brick src paths (kept in sync via the shared computation).
        existing_paths: list[str] = settings["python.autoComplete.extraPaths"]
        user_folder = Settings.get_user_bricks_folder()
        system_folder = Settings.get_sys_bricks_folder()
        existing_paths = [
            path
            for path in existing_paths
            if not path.startswith(user_folder) and not path.startswith(system_folder)
        ]
        existing_paths.extend(cls.compute_brick_extra_paths())

        settings["python.autoComplete.extraPaths"] = existing_paths

        # pyrightconfig.json is the single source of truth for the analysis scope.
        # Pylance ignores these keys when that file exists and reports a warning for
        # each one, so drop any that a previous version of this CLI wrote.
        for key in cls.PYRIGHT_OWNED_SETTINGS_KEYS:
            settings.pop(key, None)

        # Always managed by the CLI: overwrite so list updates reach every dev.
        # Other keys in the file are left untouched.
        typer.echo("Setting the excluded folders...")
        settings["files.watcherExclude"] = cls.compute_watcher_exclude()
        settings["files.exclude"] = cls.compute_files_exclude()

        try:
            typer.echo("Writing the vscode settings file...")
            # Write the settings file
            with open(settings_path, "w", encoding="UTF-8") as file:
                json.dump(settings, file, indent=2)
        except Exception as err:
            typer.echo(f"Error during writing the vscode settings file: {err}", err=True)
            return

    @classmethod
    def compute_watcher_exclude(cls) -> dict:
        """Build the ``files.watcherExclude`` value.

        The watcher matches full paths, so every entry needs a trailing ``/**``.
        """
        patterns = cls.WATCHER_EXCLUDE_EXTRA + cls.NOISE_FOLDER_NAMES
        return {f"{pattern}/**": True for pattern in patterns}

    @classmethod
    def compute_files_exclude(cls) -> dict:
        """Build the ``files.exclude`` value (hides the noise folders from the Explorer).

        Unlike the watcher, this matches the folder itself, so no ``/**`` suffix.
        The git subtrees are left out: hiding them would hide ``.git`` in the tree.
        """
        return dict.fromkeys(cls.NOISE_FOLDER_NAMES, True)

    @classmethod
    def generate_vs_code_settings_json(cls, settings_path: str) -> dict:
        """Generate a new VS Code settings.json file from template."""
        # Copy the settings.json file only if it does not exist
        shutil.copyfile(os.path.join(cls.TEMPLATE_DIR, "settings.json"), settings_path)

        # Load the settings file into a dict
        with open(settings_path, encoding="UTF-8") as file:
            return json.load(file)

    @classmethod
    def compute_brick_extra_paths(cls) -> list[str]:
        """Compute the brick source paths to expose to the Python language server.

        Shared source of truth for both the VS Code ``settings.json`` extraPaths
        and the ``pyrightconfig.json`` extraPaths, so the editor (Pylance) and the
        pyright CLI resolve imports identically. Returns each brick's ``src``
        folder plus the special gws_core Streamlit / Reflex roots.
        """
        extra_paths: list[str] = []
        brick_folders = BrickService.list_brick_directories(distinct=True)

        for brick_folder in brick_folders:
            brick_src_path = os.path.join(brick_folder.path, BrickService.SOURCE_FOLDER)
            extra_paths.append(brick_src_path)

            # Add special path for gws_core Streamlit and Reflex
            if brick_folder.name == Settings.get_gws_core_brick_name():
                streamlit_path = os.path.join(brick_src_path, cls.CUSTOM_GWS_CORE_STREAMLIT_PATH)
                if os.path.exists(streamlit_path):
                    extra_paths.append(streamlit_path)

                reflex_path = os.path.join(brick_src_path, cls.CUSTOM_GWS_CORE_REFLEX_PATH)
                if os.path.exists(reflex_path):
                    extra_paths.append(reflex_path)

        return extra_paths

    @classmethod
    def get_pyright_config_file_path(cls) -> str:
        """Get the pyrightconfig.json file path (user folder root)."""
        return os.path.join(Settings.get_user_folder(), "pyrightconfig.json")

    @classmethod
    def config_pyright_config_json(cls) -> None:
        """Generate the pyrightconfig.json file so the pyright CLI matches Pylance.

        Pyright's CLI ignores ``.vscode/settings.json``; it reads its own
        ``pyrightconfig.json``. We mirror the editor configuration: the same brick
        ``extraPaths`` (so imports resolve identically) and the active virtual
        environment, detected dynamically from the running interpreter
        (``sys.prefix``), so the file stays correct across environments.
        """
        typer.echo("Configuring pyrightconfig.json file...")

        # Setting "exclude" replaces pyright's own defaults rather than extending
        # them, so they are restored explicitly. "**/.*" only covers dotted entries
        # at the root of each search path, hence the explicit "**/.states" & co.
        pyright_default_exclude = ["**/node_modules", "**/__pycache__", "**/.*"]
        exclude = pyright_default_exclude + [
            pattern for pattern in cls.NOISE_FOLDER_NAMES if pattern not in pyright_default_exclude
        ]

        config: dict = {
            "typeCheckingMode": "basic",
            "exclude": exclude,
            "extraPaths": cls.compute_brick_extra_paths(),
        }

        # Detect the active virtual environment from the running interpreter.
        # sys.prefix points to the venv root when running inside one; pyright wants
        # the parent folder (venvPath) plus the venv folder name (venv).
        venv_prefix = sys.prefix
        if venv_prefix != sys.base_prefix:
            config["venvPath"] = os.path.dirname(venv_prefix)
            config["venv"] = os.path.basename(venv_prefix)

        config_path = cls.get_pyright_config_file_path()
        try:
            typer.echo("Writing the pyrightconfig.json file...")
            with open(config_path, "w", encoding="UTF-8") as file:
                json.dump(config, file, indent=2)
        except Exception as err:
            typer.echo(f"Error during writing the pyrightconfig.json file: {err}", err=True)

    @classmethod
    def install_pytest_config(cls) -> None:
        """Install pytest configuration files (conftest.py and pyproject.toml) to the user folder.

        These files enable running tests from VSCode's Test Explorer.
        """
        typer.echo("Installing pytest configuration...")

        user_folder = Settings.get_user_folder()

        # Always override conftest.py and pyproject.toml
        shutil.copyfile(
            os.path.join(cls.TEMPLATE_DIR, "conftest.py"),
            os.path.join(user_folder, "conftest.py"),
        )
        shutil.copyfile(
            os.path.join(cls.TEMPLATE_DIR, "pyproject.toml"),
            os.path.join(user_folder, "pyproject.toml"),
        )

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
