# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
import sys

from .core.utils.settings import Settings

LAB_DIR = os.path.join("/lab")
if os.path.exists(os.path.join(LAB_DIR, "./.core")):
    BASE_WORKSPACE_DIR = os.path.join(LAB_DIR, "./.core")
else:
    BASE_WORKSPACE_DIR = os.path.join(LAB_DIR, "./core")

BASE_BRICK_DIR = os.path.join(BASE_WORKSPACE_DIR, "./bricks")
BASE_EXTERN_DIR = os.path.join(BASE_WORKSPACE_DIR, "./externs")
USER_WORKSPACE_DIR = os.path.join(LAB_DIR, "./user")
USER_BRICK_DIR = os.path.join(USER_WORKSPACE_DIR, "./bricks/")
USER_MAIN_DIR = os.path.join(USER_WORKSPACE_DIR, "./main/")
USER_EXTERN_DIR = os.path.join(USER_WORKSPACE_DIR, "./externs")

DIR_TOKENS = dict(
    LAB_DIR=LAB_DIR,
    BASE_WORKSPACE_DIR=BASE_WORKSPACE_DIR,
    BASE_BRICK_DIR=BASE_BRICK_DIR,
    BASE_EXTERN_DIR=BASE_EXTERN_DIR,
    USER_WORKSPACE_DIR=USER_WORKSPACE_DIR,
    USER_BRICK_DIR=USER_BRICK_DIR,
    USER_EXTERN_DIR=USER_EXTERN_DIR,
)

loaded_bricks = []


def read_brick_name(cwd):
    brick_name = None
    file_path = os.path.join(cwd, "settings.json")
    with open(file_path) as f:
        try:
            settings = json.load(f)
        except Exception as err:
            raise Exception(
                f"Error while parsing the setting JSON file. Please check file setting file '{file_path}'") from err

    brick_name = settings.get("name", None)
    if brick_name is None:
        raise Exception(
            f"The brick name is required. Please check file setting file '{file_path}")

    return brick_name


def _update_json(d, u):
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = _update_json(d.get(k, {}), v)
        elif isinstance(v, list):
            d[k] = d.get(k, []) + v
        else:
            d[k] = v
    return d


def _replace_dir_tokens(path):
    for k in DIR_TOKENS:
        path = path.replace(f"${{{k}}}", DIR_TOKENS[k])

    return path


def _update_relative_paths(dep_cwd, dep_settings):

    for k in dep_settings:
        if k.endswith("_dir"):
            if not isinstance(dep_settings[k], str):
                raise Exception(
                    "Error while parsing setting. Parameter " + k + " must be a string")

            dep_settings[k] = _replace_dir_tokens(dep_settings[k])
            if dep_settings[k].startswith("."):
                dep_settings[k] = os.path.abspath(
                    os.path.join(dep_cwd, dep_settings[k]))

    for k in dep_settings.get("dirs", {}):
        if not isinstance(dep_settings["dirs"][k], str):
            raise Exception(
                "Error while parsing setting. Parameter " + k + " must be a string")

        dep_settings["dirs"][k] = _replace_dir_tokens(dep_settings["dirs"][k])
        if dep_settings["dirs"][k].startswith("."):
            dep_settings["dirs"][k] = os.path.abspath(
                os.path.join(dep_cwd, dep_settings["dirs"][k]))

    return dep_settings


def _find_brick(name):
    dep_cwd = os.path.join(BASE_BRICK_DIR, name)
    if os.path.exists(dep_cwd):
        return dep_cwd

    dep_cwd = os.path.join(USER_BRICK_DIR, name)
    if os.path.exists(dep_cwd):
        return dep_cwd

    return None


def _find_lab(name):
    dep_cwd = os.path.join(USER_MAIN_DIR, name)
    if os.path.exists(dep_cwd):
        return dep_cwd

    return None


def _parse_settings(brick_cwd: str = None, brick_name: str = None, brick_settings_file_path: str = None):
    if brick_name in loaded_bricks:
        return {}

    loaded_bricks.append(brick_name)

    if brick_cwd is None:
        raise Exception("Parameter brick_cwd is required")

    if not os.path.exists(brick_settings_file_path):
        raise Exception(
            f"The setting file of brick '{brick_name}' is not found. Please check file '{brick_settings_file_path}'")

    with open(brick_settings_file_path) as f:
        try:
            settings = json.load(f)
            if settings.get("name", None) is None:
                raise Exception(
                    f"The name of the brick is not found. Please check file '{brick_settings_file_path}'")
        except Exception as err:
            raise Exception(
                f"Error while parsing the setting JSON file. Please check file '{brick_settings_file_path}'") from err

    settings["extern_dirs"] = {}
    settings["dependency_dirs"] = {}

    # loads extern libs
    for dep in settings.get("externs", {}).keys():
        if "/" in dep:
            if dep.startswith("/"):
                dep_cwd = dep
            else:
                dep_cwd = os.path.join(brick_cwd, dep)
        else:
            dep_cwd = os.path.join(BASE_EXTERN_DIR, dep)
            if not os.path.exists(dep_cwd):
                dep_cwd = os.path.join(USER_EXTERN_DIR, dep)
                if not os.path.exists(dep_cwd):
                    raise Exception(f"The extern lib {dep} is not found")

        settings["extern_dirs"][dep] = os.path.abspath(dep_cwd)
        sys.path.insert(0, dep_cwd)

    # allows loading the current brick
    if not brick_name in settings["dependencies"]:
        settings["dependencies"].update({brick_name: "DEFAULT_ORIGIN"})

    # loads dependencies
    for dep in settings.get("dependencies", {}).keys():
        dep_cwd = _find_brick(dep)

        if dep_cwd is None:
            dep_cwd = _find_lab(dep)

        if dep_cwd is None:
            continue

        sys.path.insert(0, dep_cwd)

        settings["dependency_dirs"][dep] = os.path.abspath(dep_cwd)
        dep_setting_file = os.path.join(dep_cwd, "./settings.json")

        dep_exist = (dep != brick_name)

        if dep_exist:
            dep_settings = _parse_settings(
                brick_cwd=dep_cwd, brick_name=dep, brick_settings_file_path=dep_setting_file)
            if len(dep_settings) > 0:
                dep_settings = _update_relative_paths(dep_cwd, dep_settings)
                settings = _update_json(dep_settings, settings)
        else:
            if len(settings) > 0:
                settings = _update_relative_paths(dep_cwd, settings)

    # uniquefy dependencies
    #settings["dependencies"] = list(set(settings["dependencies"]))
    #settings["externs"] = list(set(settings["externs"]))

    return settings


def parse_settings(brick_cwd: str = None):
    brick_name = read_brick_name(brick_cwd)
    brick_settings_file_path = os.path.join(brick_cwd, "settings.json")
    default_settings = {
        "type": "brick",
        "app_dir": "./",
        "app_host": "localhost",
        "app_port": 3000,
        "externs": {},
        "dependencies": {},
        "__cwd__": brick_cwd
    }

    settings = _update_json(default_settings, _parse_settings(
        brick_cwd=brick_cwd, brick_name=brick_name, brick_settings_file_path=brick_settings_file_path))
    return settings


def load_settings(brick_cwd: str = None):
    settings = parse_settings(brick_cwd)
    Settings.init(settings)