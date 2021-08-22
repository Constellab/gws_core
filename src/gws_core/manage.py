# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
import re
import sys
import importlib
from .core.utils.settings import Settings

class SettingsLoader:
    """
    Settings loader

    Recursively loads setting of all bricks in the user workspace.
    Add these bricks to Python path to have them available in the Application
    """

    USER_WORKSPACE_DIR = "/lab/user/"
    all_settings = {
        "cwd": "",
        "modules": {},
    }

    # -- L --

    @classmethod
    def load_settings(cls, cwd: str = None):
        cls.parse_settings(cwd)
        cls.all_settings["cwd"] = cwd
        Settings.init(cls.all_settings)

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
    def parse_variables(cwd, variables):
        for key, value in variables.items():
            value = value.replace("{LAB_DIR}", "/lab")
            value = value.replace("{DATA_DIR}", "/data")
            value = value.replace("{CURRENT_DIR}", cwd)
            variables[key] = value

    @classmethod
    def parse_settings(cls, cwd):
        repo_name = cwd.strip("/").split("/")[-1]
        file_path = os.path.join(cwd, "settings.json")
        is_brick = os.path.exists(file_path)
        if is_brick:
            with open(file_path) as fp:
                try:
                    settings = json.load(fp)
                except Exception as err:
                    raise Exception(
                        f"Error while parsing the setting JSON file. Please check file setting file '{file_path}'") from err

            # parse variables
            cls.parse_variables(cwd, settings.get("variables"))

            # parse git packages
            cls._update_dict(cls.all_settings, settings)
            git_env = settings["environment"].get("git",[])
            for channel in git_env:
                for package in channel.get("packages"):
                    repo, _, _ = cls.parse_git_package(package)
                    repo_dir = os.path.join(cls.USER_WORKSPACE_DIR, "bricks", repo)
                    cls.parse_settings(repo_dir)

            if repo_name not in cls.all_settings["modules"]:
                sys.path.insert(0, os.path.abspath(cwd))
                cls.all_settings["modules"][repo_name] = {
                    "path": cwd,
                    "type": "brick,git"
                }

            pip_env = settings["environment"].get("pip",[])
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
                    path = os.path.dirname(module.__path__)
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
