# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import importlib
import json
import os
import re
import subprocess
import sys
from typing import Dict, List, Literal

import click
from gws_core.core.utils.logger import Logger

from . import runner
from .brick.brick_service import BrickService
from .core.utils.settings import ModuleInfo, Settings

RepoType = Literal["git", "pip", "app"]


class SettingsLoader:
    """
    Settings loader

    Recursively loads setting of all bricks in the user workspace.
    Add these bricks to Python path to have them available in the Application
    """

    LAB_WORKSPACE_DIR = "/lab"
    DATA_DIR = "/lab"

    SYS_WORKSPACE_DIR: str = os.path.join(LAB_WORKSPACE_DIR, '.sys')
    USER_WORKSPACE_DIR: str = os.path.join(LAB_WORKSPACE_DIR, 'user')

    USER_BRICKS_FOLDER = os.path.join(USER_WORKSPACE_DIR, 'bricks')
    NOTEBOOK_FOLDER = os.path.join(USER_WORKSPACE_DIR, "notebooks")
    SYS_BRICKS_FOLDER = os.path.join(SYS_WORKSPACE_DIR, 'bricks')
    EXTERNAL_LIB_FOLDER = os.path.join(SYS_WORKSPACE_DIR, "lib")

    SOURCE_FOLDER_NAME = "src"
    START_APP_FOLDER = 'app'

    ROOT_CWD: str = None
    IS_PROD: bool = None

    all_settings = {
        "cwd": "",
        "modules": {},
    }

    @classmethod
    def load_settings(cls) -> None:
        cls._init()
        cls._load_notebook()
        cls.all_settings["pip_freeze"] = cls.pip_freeze().split()
        Settings.init(cls.all_settings)

        # /!\ Ensure that all bricks' modules are loaded on Application startup
        # Is important to be able to traverse all Bricks/Model/Object inheritors
        BrickService.import_all_bricks_in_python()

    @classmethod
    def _init(cls):
        module_name = cls.ROOT_CWD.strip("/").split("/")[-1]
        cls.parse_settings(module_name, cls.ROOT_CWD, is_brick=True, repo_type="app")

        # in dev mode also load bricks from the user bricks folder
        if not cls.IS_PROD:
            user_bricks = Settings.get_user_bricks_folder()
            Logger.info(f"Checking for dev bricks in '{user_bricks}' folder")

            # loop thourgh all direct sub folder of the user bricks folder
            for folder in os.listdir(user_bricks):
                folder_path = os.path.join(user_bricks, folder)
                # if the brick was alreayd loaded, skip it
                if folder in cls.all_settings["modules"]:
                    continue
                if os.path.isdir(folder_path) and BrickService.folder_is_brick(folder_path):
                    Logger.info(f"Loading dev brick '{folder}' from '{folder_path}'")
                    cls.parse_settings(folder, folder_path, is_brick=True, repo_type="git")
                else:
                    Logger.warning(
                        f"{Settings.get_user_bricks_folder()} folder should only contain bricks, please remove {folder} element.")

        cls.all_settings["cwd"] = cls.ROOT_CWD

    @classmethod
    def _load_notebook(cls):
        if not os.path.exists(cls.NOTEBOOK_FOLDER):
            return
        dirs = os.listdir(cls.NOTEBOOK_FOLDER)
        for file_name in dirs:
            if file_name.startswith("_") or file_name.startswith("."):
                continue
            file_path = os.path.join(cls.NOTEBOOK_FOLDER, file_name)
            if os.path.isdir(file_path):
                sys.path.insert(0, file_path)

        cls.all_settings["modules"]["notebook"] = {
            "path": cls.NOTEBOOK_FOLDER,
            "is_brick": False,
            "type": "notebook"
        }

    @classmethod
    def parse_variables(cls, repo_name: str, cwd: str, variables: Dict[str, str]) -> Dict[str, str]:
        for key, value in variables.items():
            value = value.replace("${LAB_DIR}", cls.LAB_WORKSPACE_DIR)
            value = value.replace("${DATA_DIR}", cls.DATA_DIR)
            value = value.replace("${CURRENT_DIR}", cwd)
            value = value.replace("${CURRENT_BRICK}", repo_name)
            variables[key] = value

        return variables

    @classmethod
    def parse_settings(cls, module_name: str, module_path: str, is_brick,
                       repo_type: RepoType, channel_source=""):
        channel_source = re.sub(r"((https?|ssh)://)(.+@)?(.+)", r"\1\4", channel_source)

        # if the package is already loaded, skip it
        if module_name in cls.all_settings["modules"]:
            return

        if is_brick:
            cls._load_brick(module_path, module_name, repo_type, channel_source)
        else:
            cls._load_package(module_path, module_name, channel_source)

    @classmethod
    def _load_brick(cls, brick_path: str, brick_name: str, repo_type: RepoType, channel_source: str) -> None:

        brick_module: ModuleInfo = {
            "name": brick_name,
            "path": brick_path,
            "repo_type": repo_type,
            # we don't consider app as a brick
            "is_brick":  brick_name != cls.START_APP_FOLDER,
            "source": channel_source,
            "repo_commit": None,
            "version": None,
            "error": None
        }

        if not os.path.exists(brick_path):
            brick_module["error"] = f"Folder '{brick_path}' for brick '{brick_name}' is not found. Skipping brick."
            Logger.error(brick_module["error"])
            cls._save_module(brick_module)
            return

        # read settings file
        file_path = os.path.join(brick_path, "settings.json")
        with open(file_path, 'r', encoding='utf-8') as fp:
            try:
                settings_data: dict = json.load(fp)
            except Exception as err:
                Logger.error(f"Error: cannot parse the the settings file of brick '{brick_name}'")
                Logger.log_exception_stack_trace(err)
                brick_module["error"] = f"Error: cannot parse the the settings file of brick '{brick_name}'. Error {err}"
                cls._save_module(brick_module)
                return

        # get brick version
        if not settings_data.get('version'):
            brick_module["error"] = f"Missing version in settings.json for brick {brick_name}. Skipping brick."
            cls._save_module(brick_module)
            return

        brick_module["version"] = settings_data.get('version')

        # add src folder to python path
        sys.path.insert(0, os.path.join(brick_path, cls.SOURCE_FOLDER_NAME))

        # get brick commit and version
        brick_module["repo_commit"] = cls.get_git_commit(brick_path) if repo_type == "git" else ""
        cls._save_module(brick_module)

        # parse variables
        if not "variables" in settings_data:
            settings_data["variables"] = {}
        cls.parse_variables(brick_name, brick_path, settings_data["variables"])

        cls._update_dict(cls.all_settings, settings_data)

        # loads git packages
        git_env = settings_data["environment"].get("git", [])
        cls._load_git_dependencies(git_env)

        # loads pip packages
        pip_env = settings_data["environment"].get("pip", [])
        cls._load_pip_dependencies(pip_env)

    @classmethod
    def _load_git_dependencies(cls, git_env: List[dict]) -> None:

        for channel in git_env:
            channel_source = channel["source"]
            for package in channel.get("packages"):
                module_name = package["name"]
                is_brick = package.get("is_brick", False)

                # import brick from user workspace or system workspace
                if is_brick:
                    repo_dir = os.path.join(cls.USER_BRICKS_FOLDER, module_name)
                    if not os.path.exists(repo_dir):
                        repo_dir = os.path.join(cls.SYS_BRICKS_FOLDER, module_name)
                        if not os.path.exists(repo_dir):
                            # set the dir to original location, the error is handled in parse settings
                            repo_dir = os.path.join(cls.USER_BRICKS_FOLDER, module_name)
                # import external library
                else:
                    repo_dir = os.path.join(cls.EXTERNAL_LIB_FOLDER, module_name)
                cls.parse_settings(module_name, repo_dir, is_brick, repo_type="git", channel_source=channel_source)

    @classmethod
    def _load_pip_dependencies(cls, pip_env: List[dict]) -> None:

        for channel in pip_env:
            channel_source = channel["source"]
            for package in channel.get("packages"):
                module_name = package["name"]
                is_brick = package.get("is_brick", False)
                if module_name not in sys.modules:
                    Logger.info(f"Skipping pip package '{module_name}'")
                    continue
                module = importlib.import_module(module_name)
                module_dir = os.path.abspath(module.__file__)
                cls.parse_settings(module_name, module_dir, is_brick, repo_type="pip", channel_source=channel_source)

                # TO uncomment when pip brick will be available
                # repo = cls._pip_package_to_module_name(package["name"])
                # is_brick = package.get("is_brick", False)

                # module = None
                # if repo in sys.modules:
                #     module = sys.modules[repo]
                # else:
                #     Logger.info(f"Skipping pip package '{repo}'")
                #     continue
                #     # Logger.info(f"Loading pip package '{repo}'")
                #     # module = importlib.import_module(repo)

                # repo_dir = os.path.abspath(module.__path__[0])
                # cls.parse_settings(repo_dir, is_brick, repo_type="pip", channel_source=channel_source)

    @classmethod
    def _load_package(cls, package_path: str, package_name: str, channel_source: str) -> None:

        brick_module: ModuleInfo = {
            "name": package_name,
            "path": package_path,
            "repo_type": "",
            # we don't consider app as a brick
            "is_brick":  False,
            "source": channel_source,
            "repo_commit": None,
            "version": None,
            "error": None
        }

        if not os.path.exists(package_path):
            error = f"Folder '{package_path}' for package '{package_name}' is not found. Skipping package."
            Logger.error(error)
            brick_module["error"] = error
            cls._save_module(brick_module)
            return

        # get brick commit
        brick_module["repo_commit"] = cls.get_git_commit(package_path)

        # loading module
        sys.path.insert(0, os.path.abspath(package_path))
        cls._save_module(brick_module)

    @classmethod
    def _save_module(cls, module_info: ModuleInfo) -> None:
        cls.all_settings["modules"][module_info["name"]] = module_info

    @classmethod
    def _pip_package_to_module_name(cls, pip_package: str) -> str:
        """Convert the pip package name to the module name
        """
        return pip_package.replace('-', '_')

    @classmethod
    def _update_dict(cls, d, u):
        for key, value in u.items():
            if isinstance(value, dict):
                d[key] = cls._update_dict(d.get(key, {}), value)
            elif isinstance(value, list):
                d[key] = d.get(key, []) + value
            else:
                d[key] = value
        return d

    @classmethod
    def pip_freeze(cls):
        return subprocess.check_output(["python3", "-m", "pip", "freeze"], stderr=subprocess.DEVNULL, text=True)

    @classmethod
    def get_git_commit(cls, cwd):
        if not os.path.exists(os.path.join(cwd, ".git")):
            return ""

        git_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=cwd, stderr=subprocess.DEVNULL, text=True)

        if not git_commit:
            return ""
        return git_commit.strip()


def load_settings(cwd: str) -> None:
    print("/!\ manage.load_settings() is deprecated, please remove it and use manage.start_app() instead")
    start_app(cwd)


def start_app(cwd: str) -> None:
    SettingsLoader.ROOT_CWD = cwd
    _start_app()


@click.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True
))
@click.pass_context
@click.option('--test', default="",
              help='The name test file to launch (regular expression). Enter "all" to launch all the tests')
@click.option('--cli', default="", help='Command to run using the command line interface')
@click.option('--cli_test', is_flag=True, help='Use command line interface in test mode')
@click.option('--runserver', is_flag=True, help='Starts the server')
@click.option('--runmode', default="dev", help='Starting mode (dev or prod). Defaults to dev')
@click.option('--notebook', is_flag=True, help='Starts the for notebook')
@click.option('--port', default="3000", help='Server port', show_default=True)
@click.option('--log_level', default="INFO", help='Level for the logs', show_default=True)
@click.option('--show_sql', is_flag=True, help='Log sql queries in the console')
@click.option('--reset_env', is_flag=True, help='Reset environment')
def _start_app(ctx, test: bool, cli, cli_test: bool, runserver: bool,
               runmode, notebook: bool, port, log_level: str, show_sql: bool, reset_env: bool):
    is_prod = runmode == "prod"
    SettingsLoader.IS_PROD = is_prod
    SettingsLoader.load_settings()

    is_test = bool(test or cli_test)

    runner.call(is_prod, is_test, test, cli, runserver, notebook, port, log_level, show_sql, reset_env)
