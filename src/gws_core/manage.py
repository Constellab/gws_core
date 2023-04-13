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

from gws_core.brick.brick_dto import BrickInfo
from gws_core.core.utils.logger import Logger
from gws_core.notebook.notebook import Notebook

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

    GIT_INSTALLATION_FILE = ".gws-git-installation.json"
    SETTINGS_JSON_FILE = "settings.json"

    ROOT_CWD: str = None
    IS_PROD: bool = None

    all_settings = {
        "cwd": "",
        "modules": {},
    }

    settings: Settings = None

    @classmethod
    def load_settings(cls) -> None:
        cls.settings = Settings.init()
        cls._init()

        cls.settings.set_cwd(cls.ROOT_CWD)
        cls.settings.set_pip_freeze(cls.pip_freeze().split())
        # save the settings
        cls.settings.save()

        # /!\ Ensure that all bricks' modules are loaded on Application startup
        # Is important to be able to traverse all Bricks/Model/Object inheritors
        BrickService.import_all_bricks_in_python()

    @classmethod
    def _init(cls):

        # read settings file
        settings: dict = None
        try:
            settings = cls._read_brick_settings(cls.ROOT_CWD)
        except Exception as err:
            Logger.error(
                f"Error: cannot parse the main settings file under '{cls.ROOT_CWD}'")
            raise err

        bricks = settings["environment"].get("bricks", [])
        # load all the bricks dependencies
        cls._load_brick_dependencies(bricks, parent_name=None)

        # in dev mode also load bricks from the user bricks folder
        if not cls.IS_PROD:
            user_bricks = Settings.get_user_bricks_folder()
            Logger.info(f"Checking for dev bricks in '{user_bricks}' folder")

            # loop thourgh all direct sub folder of the user bricks folder
            for folder in os.listdir(user_bricks):
                folder_path = os.path.join(user_bricks, folder)
                # if the brick was alreayd loaded, skip it
                if folder in cls.settings.get_bricks():
                    continue
                if os.path.isdir(folder_path) and BrickService.folder_is_brick(folder_path):
                    Logger.info(
                        f"Loading dev brick '{folder}' from '{folder_path}'")
                    cls.load_brick(folder)
                else:
                    Logger.warning(
                        f"{Settings.get_user_bricks_folder()} folder should only contain bricks, please remove {folder} element.")

    @classmethod
    def load_brick(cls, brick_name: str, parent_name: str = None) -> None:

        # repo dir is the path to the brick folder
        # if the brick is not found in the user workspace, we look for it in the system workspace
        brick_path = os.path.join(cls.USER_BRICKS_FOLDER, brick_name) if os.path.exists(
            os.path.join(cls.USER_BRICKS_FOLDER, brick_name)) else os.path.join(cls.SYS_BRICKS_FOLDER, brick_name)

        # if the package is already loaded, skip it
        if brick_name in cls.settings.get_bricks():
            return

        brick_module: BrickInfo = {
            "path": brick_path,
            "name": brick_name,
            "version": None,
            "repo_type": None,
            "repo_commit": None,
            "parent_name": parent_name,
            "error": None
        }

        if not os.path.exists(brick_path):
            brick_module["error"] = f"Folder '{brick_path}' for brick '{brick_name}' is not found. Skipping brick."
            Logger.error(brick_module["error"])
            cls._save_brick(brick_module)
            return

        # read settings file
        file_path = os.path.join(brick_path, "settings.json")
        with open(file_path, 'r', encoding='utf-8') as fp:
            try:
                settings_data: dict = json.load(fp)
            except Exception as err:
                Logger.error(
                    f"Error: cannot parse the the settings file of brick '{brick_name}'")
                Logger.log_exception_stack_trace(err)
                brick_module[
                    "error"] = f"Error: cannot parse the the settings file of brick '{brick_name}'. Error {err}"
                cls._save_brick(brick_module)
                return

        # get brick version
        if not settings_data.get('version'):
            brick_module[
                "error"] = f"Missing version in settings.json for brick {brick_name}. Skipping brick."
            cls._save_brick(brick_module)
            return

        brick_module["version"] = settings_data.get('version')

        # add src folder to python path
        sys.path.insert(0, os.path.join(brick_path, cls.SOURCE_FOLDER_NAME))

        # get brick commit and version
        git_commit = cls._get_git_commit(brick_path)
        brick_module["repo_commit"] = git_commit
        brick_module["repo_type"] = 'git' if git_commit else 'pip'
        cls._save_brick(brick_module)

        # parse and save variables
        cls._save_brick_variables(
            brick_name, brick_path, settings_data["variables"])

        # loads git packages
        git_env = settings_data["environment"].get("git", [])
        cls._load_git_dependencies(git_env, parent_name=brick_name)

        # loads pip packages
        pip_env = settings_data["environment"].get("pip", [])
        cls._load_pip_dependencies(pip_env)

        bricks = settings_data["environment"].get("bricks", [])
        cls._load_brick_dependencies(bricks, parent_name=brick_name)

    @classmethod
    def _read_brick_settings(cls, brick_path: str) -> dict:
        file_path = os.path.join(brick_path, cls.SETTINGS_JSON_FILE)
        with open(file_path, 'r', encoding='utf-8') as fp:
            return json.load(fp)

    @classmethod
    def _load_brick_dependencies(cls, bricks: List[dict], parent_name: str = None) -> None:

        for brick in bricks:
            brick_name = brick["name"]

            cls.load_brick(brick_name=brick_name, parent_name=parent_name)

    @classmethod
    def _load_git_dependencies(cls, git_env: List[dict], parent_name: str) -> None:

        for channel in git_env:
            channel_source = channel["source"]
            for package in channel.get("packages"):
                module_name = package["name"]
                is_brick = package.get("is_brick", False)

                # import brick from user workspace or system workspace
                if is_brick:  # TODO to remove once all brick are under bricks object
                    cls.load_brick(module_name, parent_name=parent_name)
                else:
                    repo_dir = os.path.join(
                        cls.EXTERNAL_LIB_FOLDER, module_name)
                    cls._load_package(package_name=module_name, package_path=repo_dir,
                                      channel_source=channel_source, repo_type="git")

    @classmethod
    def _load_pip_dependencies(cls, pip_env: List[dict]) -> None:

        for channel in pip_env:
            channel_source = channel["source"]
            for package in channel.get("packages"):
                module_name = package["name"]

                if module_name not in sys.modules:
                    Logger.info(f"Skipping pip package '{module_name}'")
                    continue
                module = importlib.import_module(module_name)
                module_dir = os.path.abspath(module.__file__)
                cls._load_package(package_name=module_name, package_path=module_dir,
                                  channel_source=channel_source, repo_type="pip")

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
    def _load_package(cls, package_path: str, package_name: str, channel_source: str, repo_type: Literal['git', 'pip']) -> None:

        # if the package is already loaded, skip it
        if package_name in cls.settings.get_modules():
            return

        brick_module: ModuleInfo = {
            "path": package_path,
            "name": package_name,
            "source": channel_source,
            "version": None,
            "repo_type": "",
            "repo_commit": None,
            "parent_name": None,
            "error": None
        }

        if not os.path.exists(package_path):
            error = f"Folder '{package_path}' for package '{package_name}' is not found. Skipping package."
            Logger.error(error)
            brick_module["error"] = error
            cls._save_module(brick_module)
            return

        # get brick commit
        brick_module["repo_commit"] = cls._get_git_commit(package_path)

        # loading module
        # for git repo, if an src folder is present, add it to the path
        # otherwise add the repo folder to the path
        sub_src_folder = os.path.join(package_path, cls.SOURCE_FOLDER_NAME)
        if repo_type == 'git' and os.path.exists(sub_src_folder):
            sys.path.insert(0, os.path.abspath(sub_src_folder))
        else:
            sys.path.insert(0, os.path.abspath(package_path))
        cls._save_module(brick_module)

    @classmethod
    def _save_brick_variables(cls, repo_name: str, cwd: str, variables: Dict[str, str]) -> None:
        """Save the repo variable in the settings and replace the variables with the correct value.
        """
        for key, value in variables.items():
            value = value.replace("${LAB_DIR}", cls.LAB_WORKSPACE_DIR)
            value = value.replace("${DATA_DIR}", cls.DATA_DIR)
            value = value.replace("${CURRENT_DIR}", cwd)
            value = value.replace("${CURRENT_BRICK}", repo_name)
            cls.settings.set_variable(key, value)

    @classmethod
    def _save_module(cls, module_info: ModuleInfo) -> None:
        cls.settings.add_module(module_info)

    @classmethod
    def _save_brick(cls, brick_info: BrickInfo) -> None:
        cls.settings.add_brick(brick_info)

    @classmethod
    def _pip_package_to_module_name(cls, pip_package: str) -> str:
        """Convert the pip package name to the module name
        """
        return pip_package.replace('-', '_')

    @classmethod
    def pip_freeze(cls):
        return subprocess.check_output(["python3", "-m", "pip", "freeze"], stderr=subprocess.DEVNULL, text=True)

    @classmethod
    def _get_git_commit(cls, cwd) -> str:
        """retrieve the git commit info from GIT_INSTALLATION_FILE file

        :param cwd: _description_
        :type cwd: _type_
        :return: _description_
        :rtype: str
        """

        git_install_path = os.path.join(cwd, cls.GIT_INSTALLATION_FILE)

        if not os.path.exists(git_install_path):
            return ""

        with open(git_install_path, 'r', encoding='utf-8') as fp:
            try:
                settings_data: dict = json.load(fp)
                return settings_data.get('git_hash')
            except Exception:
                Logger.error(
                    f"Error: cannot parse the the gws-git-installation.json of git package '{cwd}'")
                return None


def load_settings(cwd: str) -> None:
    print("/!\ manage.load_settings() is deprecated, please remove it and use manage.start_app() instead")
    start_app(cwd)


def start_app(cwd: str) -> None:
    SettingsLoader.ROOT_CWD = cwd
    _start_app_console()


def start_notebook(cwd: str, log_level: str = 'INFO') -> None:
    SettingsLoader.ROOT_CWD = cwd
    _start_app(test=False, cli='', runserver=False, is_prod=False, notebook=True,
               port='3000', log_level=log_level, show_sql=False, reset_env=False)
    Notebook.init_complete()


@click.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True
))
@click.pass_context
@click.option('--test', default="",
              help='The name test file to launch (regular expression). Enter "all" to launch all the tests')
@click.option('--cli', default="", help='Command to run using the command line interface')
@click.option('--runserver', is_flag=True, help='Starts the server')
@click.option('--runmode', default="dev", help='Starting mode (dev or prod). Defaults to dev')
@click.option('--notebook', is_flag=True, help='Starts the for notebook')
@click.option('--port', default="3000", help='Server port', show_default=True)
@click.option('--log_level', default="INFO", help='Level for the logs', show_default=True)
@click.option('--show_sql', is_flag=True, help='Log sql queries in the console')
@click.option('--reset_env', is_flag=True, help='Reset environment')
def _start_app_console(ctx, test: bool, cli: str, runserver: bool,
                       runmode, notebook: bool, port: str, log_level: str, show_sql: bool, reset_env: bool):
    is_prod = runmode == "prod"

    _start_app(test, cli, runserver, is_prod, notebook,
               port, log_level, show_sql, reset_env)


def _start_app(test: str, cli: str, runserver: bool,
               is_prod: bool, notebook: bool, port: str,
               log_level: str, show_sql: bool, reset_env: bool):
    SettingsLoader.IS_PROD = is_prod
    SettingsLoader.load_settings()

    runner.call(is_prod, test, cli, runserver, notebook,
                port, log_level, show_sql, reset_env)
