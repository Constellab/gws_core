# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import importlib
import json
import os
import re
import sys

from .core.utils.settings import Settings


class SettingsLoader:
    """
    Settings loader

    Recursively loads setting of all bricks in the user workspace.
    Add these bricks to Python path to have them available in the Application
    """

    LAB_WORKSPACE_DIR = "/lab"
    NOTEBOOK_DIR = os.path.join(LAB_WORKSPACE_DIR, "user/notebooks")
    all_settings = {
        "cwd": "",
        "modules": {},
    }

    # -- L --

    @classmethod
    def _load_bricks(cls, cwd: str = None):
        cls.parse_settings(cwd)
        cls.all_settings["cwd"] = cwd

    @classmethod
    def _load_notebook(cls):
        if not os.path.exists(cls.NOTEBOOK_DIR):
            return
        dirs = os.listdir(cls.NOTEBOOK_DIR)
        for file_name in dirs:
            if file_name.startswith("_") or file_name.startswith("."):
                continue
            file_path = os.path.join(cls.NOTEBOOK_DIR, file_name)
            if os.path.isdir(file_path):
                sys.path.insert(0, file_path)

        cls.all_settings["modules"]["notebook"] = {
            "path": cls.NOTEBOOK_DIR,
            "type": "notebook"
        }

    @classmethod
    def load_settings(cls, cwd: str = None):
        cls._load_bricks(cwd)
        cls._load_notebook()
        Settings.init(cls.all_settings)

        # /!\ Ensure that all bricks' modules are loaded on Application startup
        # Is important to be able to traverse all Bricks/Model/Object inheritors
        from .core.utils.utils import Utils
        Utils.import_all_modules()

    # -- P --

    @staticmethod
    def parse_git_package(string: str) -> str:
        tab = re.findall(r"\[.+\]$", string)
        if tab:
            string = string.replace(tab[0], "")
            commit_sha = re.match(r".*(c|commit)\s*=\s*([A-Za-z0-9]+).*", tab[0])[2]
            branch = re.match(r".*(b|branch)\s*=\s*([A-Za-z0-9]+).*", tab[0])[2]
            if commit_sha == "latest":
                commit_sha = None
            return string, commit_sha, branch
        return string, None, None

    @staticmethod
    def parse_variables(repo_name, cwd, variables):
        for key, value in variables.items():
            value = value.replace("{LAB_DIR}", "/lab")
            value = value.replace("{DATA_DIR}", "/data")
            value = value.replace("{CURRENT_DIR}", cwd)
            value = value.replace("{CURRENT_BRICK}", repo_name)
            variables[key] = value

    @classmethod
    def parse_settings(cls, cwd):
        repo_name = cwd.strip("/").split("/")[-1]
        file_path = os.path.join(cwd, "settings.json")
        is_brick = os.path.exists(file_path)
        if is_brick:
            with open(file_path, 'r', encoding='utf-8') as fp:
                try:
                    settings_data = json.load(fp)
                except Exception as err:
                    raise Exception(
                        f"Error while parsing the setting JSON file. Please check file setting file '{file_path}'") from err

            # parse variables
            if not "variables" in settings_data:
                settings_data["variables"] = {}
            cls.parse_variables(repo_name, cwd, settings_data["variables"])

            # parse git packages
            cls._update_dict(cls.all_settings, settings_data)
            git_env = settings_data["environment"].get("git", [])
            for channel in git_env:
                for package in channel.get("packages"):
                    repo, _, _ = cls.parse_git_package(package)
                    repo_dir = os.path.join(cls.LAB_WORKSPACE_DIR, "user", "bricks", repo)
                    if not os.path.exists(repo_dir):
                        repo_dir = os.path.join(cls.LAB_WORKSPACE_DIR, ".sys", "lib", repo)
                        if not os.path.exists(repo_dir):
                            raise Exception(f"Repository '{repo_dir}' is not found")

                    cls.parse_settings(repo_dir)

            if repo_name not in cls.all_settings["modules"]:
                sys.path.insert(0, os.path.join(cwd, "src"))
                cls.all_settings["modules"][repo_name] = {
                    "path": cwd,
                    "type": "brick,git"
                }

            pip_env = settings_data["environment"].get("pip", [])
            cls._read_pip_deps(pip_env)
        else:
            if cwd not in cls.all_settings["modules"]:
                sys.path.insert(0, os.path.abspath(cwd))
                cls.all_settings["modules"][repo_name] = {
                    "path": cwd,
                    "type": "extern"
                }

    # -- R --

    @classmethod
    def _read_pip_deps(cls, pip_env: dict):
        for channel in pip_env:
            for package in channel.get("packages"):
                package = re.match(r"^([a-zA-Z]+).*", package)[1]
                if package in sys.modules:
                    module = importlib.import_module(package)
                    path = os.path.abspath(module.__file__)
                    file_path = os.path.join(path, "settings.json")
                    is_brick = os.path.exists(file_path)
                    if is_brick:
                        cls.all_settings["modules"][package] = {
                            "path": path,
                            "type": "brick,pip"
                        }

    # -- U --

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


def load_settings(cwd):
    SettingsLoader.load_settings(cwd)
