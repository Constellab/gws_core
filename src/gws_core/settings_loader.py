

import importlib
import json
import os
import subprocess
import sys
from typing import Dict, List, Literal

from gws_core.brick.brick_dto import BrickInfo
from gws_core.core.utils.logger import Logger
from gws_core.lab.system_dto import ModuleInfo

from .brick.brick_service import BrickService
from .core.utils.settings import Settings


class SettingsLoader:
    """
    Settings loader

    Recursively loads setting of all bricks in the user workspace.
    Add these bricks to Python path to have them available in the Application
    """

    LAB_WORKSPACE_DIR = "/lab"

    SYS_WORKSPACE_DIR: str = os.path.join(LAB_WORKSPACE_DIR, '.sys')
    USER_WORKSPACE_DIR: str = os.path.join(LAB_WORKSPACE_DIR, 'user')

    USER_BRICKS_FOLDER = os.path.join(USER_WORKSPACE_DIR, 'bricks')
    SYS_BRICKS_FOLDER = os.path.join(SYS_WORKSPACE_DIR, 'bricks')
    EXTERNAL_LIB_FOLDER = os.path.join(SYS_WORKSPACE_DIR, "lib")

    SOURCE_FOLDER_NAME = "src"

    GIT_INSTALLATION_FILE = ".gws-git-installation.json"
    SETTINGS_JSON_FILE = "settings.json"

    main_settings_file_path: str = None
    is_test: bool = False

    settings: Settings = None

    def __init__(self, main_settings_file_path: str,
                 is_test: bool = False) -> None:
        self.main_settings_file_path = main_settings_file_path
        self.is_test = is_test

    def load_settings(self) -> None:
        self.settings = Settings.init()
        self.settings.set_main_settings_file_path(self.main_settings_file_path)
        self.settings.set_data("is_test", self.is_test)
        self._init()

        self.settings.set_pip_freeze(self.pip_freeze().split())
        # save the settings
        self.settings.save()

        # /!\ Ensure that all bricks' modules are loaded on Application startup
        # Is important to be able to traverse all Bricks/Model/Object inheritors
        BrickService.import_all_bricks_in_python()

    def _init(self):

        # read settings file
        settings: dict = None
        try:
            settings = self._read_settings_file(self.main_settings_file_path)
        except Exception as err:
            Logger.error(
                f"Error: cannot parse the main settings file '{self.main_settings_file_path}'")
            raise err

        # load the main brick
        main_brick_name = settings.get("name")
        if not main_brick_name:
            raise Exception(
                f"Error: missing 'name' in the main settings file '{self.main_settings_file_path}'")
        self.load_brick(settings['name'], parent_name=None)

        # load all the bricks dependencies
        bricks = settings["environment"].get("bricks", [])
        self._load_brick_dependencies(bricks, parent_name=main_brick_name)

        # in dev mode also load bricks from the user bricks folder
        if Settings.is_dev_mode():
            user_bricks = Settings.get_user_bricks_folder()
            Logger.info(f"Checking for dev bricks in '{user_bricks}' folder")

            # loop thourgh all direct sub folder of the user bricks folder
            for folder in os.listdir(user_bricks):
                folder_path = os.path.join(user_bricks, folder)
                # if the brick was alreayd loaded, skip it
                if folder in self.settings.get_bricks():
                    continue
                if os.path.isdir(folder_path) and BrickService.folder_is_brick(folder_path):
                    Logger.info(
                        f"Loading dev brick '{folder}' from '{folder_path}'")
                    self.load_brick(folder)
                else:
                    Logger.warning(
                        f"{Settings.get_user_bricks_folder()} folder should only contain bricks, please remove '{folder}' file or directory.")

    def load_brick(self, brick_name: str, parent_name: str = None) -> None:

        # repo dir is the path to the brick folder
        # if the brick is not found in the user workspace, we look for it in the system workspace
        brick_path = os.path.join(self.USER_BRICKS_FOLDER, brick_name) if os.path.exists(
            os.path.join(self.USER_BRICKS_FOLDER, brick_name)) else os.path.join(self.SYS_BRICKS_FOLDER, brick_name)

        # if the package is already loaded, skip it
        if brick_name in self.settings.get_bricks():
            return

        brick_module = BrickInfo(
            path=brick_path,
            name=brick_name,
            version=None,
            repo_type=None,
            repo_commit=None,
            parent_name=parent_name,
            error=None
        )

        if not os.path.exists(brick_path):
            brick_module.error = f"Folder '{brick_path}' for brick '{brick_name}' is not found. Skipping brick."
            Logger.error(brick_module.error)
            self._save_brick(brick_module)
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
                brick_module.error = f"Error: cannot parse the the settings file of brick '{brick_name}'. Error {err}"
                self._save_brick(brick_module)
                return

        # get brick version
        if not settings_data.get('version'):
            brick_module.error = f"Missing version in settings.json for brick {brick_name}. Skipping brick."
            self._save_brick(brick_module)
            return

        brick_module.version = settings_data.get('version')

        # add src folder to python path
        sys.path.insert(0, os.path.join(brick_path, self.SOURCE_FOLDER_NAME))

        # get brick commit and version
        git_commit = self._get_git_commit(brick_path)
        brick_module.repo_commit = git_commit
        brick_module.repo_type = 'git' if git_commit else 'pip'
        self._save_brick(brick_module)

        # parse and save variables
        self._save_brick_variables(
            brick_name, brick_path, settings_data["variables"])

        # loads git packages
        git_env = settings_data["environment"].get("git", [])
        self._load_git_dependencies(git_env)

        # loads pip packages
        pip_env = settings_data["environment"].get("pip", [])
        self._load_pip_dependencies(pip_env)

        bricks = settings_data["environment"].get("bricks", [])
        self._load_brick_dependencies(bricks, parent_name=brick_name)

    def _read_settings_file(self, setting_file_path) -> dict:
        file_path = os.path.join(setting_file_path)
        with open(file_path, 'r', encoding='utf-8') as fp:
            return json.load(fp)

    def _load_brick_dependencies(self, bricks: List[dict], parent_name: str = None) -> None:

        for brick in bricks:
            brick_name = brick["name"]

            self.load_brick(brick_name=brick_name, parent_name=parent_name)

    def _load_git_dependencies(self, git_env: List[dict]) -> None:

        for channel in git_env:
            channel_source = channel["source"]
            for package in channel.get("packages"):
                module_name = package["name"]
                repo_dir = os.path.join(
                    self.EXTERNAL_LIB_FOLDER, module_name)
                self._load_package(package_name=module_name, package_path=repo_dir,
                                   channel_source=channel_source, repo_type="git")

    def _load_pip_dependencies(self, pip_env: List[dict]) -> None:

        for channel in pip_env:
            channel_source = channel["source"]
            for package in channel.get("packages"):
                module_name = package["name"]

                if module_name not in sys.modules:
                    # Logger.info(f"Skipping pip package '{module_name}'")
                    continue
                module = importlib.import_module(module_name)
                module_dir = os.path.abspath(module.__file__)
                self._load_package(package_name=module_name, package_path=module_dir,
                                   channel_source=channel_source, repo_type="pip")

                # TO uncomment when pip brick will be available
                # repo = self._pip_package_to_module_name(package["name"])
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
                # self.parse_settings(repo_dir, is_brick, repo_type="pip", channel_source=channel_source)

    def _load_package(self, package_path: str, package_name: str, channel_source: str, repo_type: Literal
                      ['git', 'pip']) -> None:

        # if the package is already loaded, skip it
        if package_name in self.settings.get_modules():
            return

        brick_module: ModuleInfo = {
            "path": package_path,
            "name": package_name,
            "source": channel_source,
            "error": None
        }

        if not os.path.exists(package_path):
            error = f"Folder '{package_path}' for package '{package_name}' is not found. Skipping package."
            Logger.error(error)
            brick_module["error"] = error
            self._save_module(brick_module)
            return

        # loading module
        # for git repo, if an src folder is present, add it to the path
        # otherwise add the repo folder to the path
        sub_src_folder = os.path.join(package_path, self.SOURCE_FOLDER_NAME)
        if repo_type == 'git' and os.path.exists(sub_src_folder):
            sys.path.insert(0, os.path.abspath(sub_src_folder))
        else:
            sys.path.insert(0, os.path.abspath(package_path))
        self._save_module(brick_module)

    def _save_brick_variables(self, repo_name: str, cwd: str, variables: Dict[str, str]) -> None:
        """Save the repo variable in the settings and replace the variables with the correct value.
        """
        for key, value in variables.items():
            value = value.replace("${LAB_DIR}", self.LAB_WORKSPACE_DIR)
            value = value.replace("${CURRENT_DIR}", cwd)
            value = value.replace("${CURRENT_BRICK}", repo_name)
            self.settings.set_variable(key, value)

    def _save_module(self, module_info: ModuleInfo) -> None:
        self.settings.add_module(module_info)

    def _save_brick(self, brick_info: BrickInfo) -> None:
        self.settings.add_brick(brick_info)

    def _pip_package_to_module_name(self, pip_package: str) -> str:
        """Convert the pip package name to the module name
        """
        return pip_package.replace('-', '_')

    def pip_freeze(self):
        return subprocess.check_output(["python3", "-m", "pip", "freeze"], stderr=subprocess.DEVNULL, text=True)

    def _get_git_commit(self, cwd) -> str:
        """retrieve the git commit info from GIT_INSTALLATION_FILE file

        :param cwd: _description_
        :type cwd: _type_
        :return: _description_
        :rtype: str
        """

        git_install_path = os.path.join(cwd, self.GIT_INSTALLATION_FILE)

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
