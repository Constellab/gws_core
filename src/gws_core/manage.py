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

from .brick.brick_service import BrickService
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
        cls.parse_settings(cwd, is_brick=True)
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
            "is_brick": False,
            "type": "notebook"
        }

    @classmethod
    def load_settings(cls, cwd: str = None):
        cls._load_bricks(cwd)
        cls._load_notebook()
        cls.all_settings["pip_freeze"] = cls.pip_freeze().split()
        Settings.init(cls.all_settings)

        # /!\ Ensure that all bricks' modules are loaded on Application startup
        # Is important to be able to traverse all Bricks/Model/Object inheritors
        BrickService.import_all_modules()

    # -- P --

    @staticmethod
    def parse_variables(repo_name, cwd, variables):
        for key, value in variables.items():
            value = value.replace("${LAB_DIR}", "/lab")
            value = value.replace("${DATA_DIR}", "/data")
            value = value.replace("${CURRENT_DIR}", cwd)
            value = value.replace("${CURRENT_BRICK}", repo_name)
            variables[key] = value

    @classmethod
    def parse_settings(cls, cwd, is_brick=False, repo_type="app"):
        repo_name = cwd.strip("/").split("/")[-1]
        if repo_name in cls.all_settings["modules"]:
            return

        if is_brick:
            # read settings file
            file_path = os.path.join(cwd, "settings.json")
            with open(file_path, 'r', encoding='utf-8') as fp:
                try:
                    settings_data = json.load(fp)
                except Exception as err:
                    raise Exception(
                        f"Error: cannot parse the the settings file of '{repo_name}'") from err

            sys.path.insert(0, os.path.join(cwd, "src"))
            cls.all_settings["modules"][repo_name] = {
                "path": cwd,
                "version": settings_data["version"],
                "is_brick": True,
                "repo_type": repo_type,
                "repo_commit": cls.get_git_commit(cwd) if repo_type == "git" else ""
            }

            # parse variables
            if not "variables" in settings_data:
                settings_data["variables"] = {}
            cls.parse_variables(repo_name, cwd, settings_data["variables"])

            # loads git packages
            cls._update_dict(cls.all_settings, settings_data)
            git_env = settings_data["environment"].get("git", [])
            for channel in git_env:
                for package in channel.get("packages"):
                    repo = package["name"]
                    is_brick = package.get("is_brick", False)
                    if is_brick:
                        repo_dir = os.path.join(cls.LAB_WORKSPACE_DIR, "user", "bricks", repo)
                        if not os.path.exists(repo_dir):
                            repo_dir = os.path.join(cls.LAB_WORKSPACE_DIR, "user", "bricks", ".lib", repo)
                            if not os.path.exists(repo_dir):
                                raise Exception(f"Repository '{repo_dir}' is not found")
                    else:
                        repo_dir = os.path.join(cls.LAB_WORKSPACE_DIR, ".sys", "lib", repo)
                        if not os.path.exists(repo_dir):
                            raise Exception(f"Repository '{repo_dir}' is not found")
                    cls.parse_settings(repo_dir, is_brick, repo_type="git")

            # loads pip packages
            pip_env = settings_data["environment"].get("pip", [])
            for channel in pip_env:
                for package in channel.get("packages"):
                    repo = package["name"]
                    is_brick = package.get("is_brick", False)
                    if repo not in sys.modules:
                        continue
                    module = importlib.import_module(repo)
                    repo_dir = os.path.abspath(module.__file__)
                    cls.parse_settings(repo_dir, is_brick, repo_type="pip")
        else:
            sys.path.insert(0, os.path.abspath(cwd))
            cls.all_settings["modules"][repo_name] = {
                "path": cwd,
                "is_brick": False,
                "repo_type": repo_type,
                "repo_commit": cls.get_git_commit(cwd),
            }

    # -- R --

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
        if os.path.exists(os.path.join(cwd, ".git")):
            return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=cwd, stderr=subprocess.DEVNULL, text=True)
        else:
            return ""


def load_settings(cwd):
    SettingsLoader.load_settings(cwd)
