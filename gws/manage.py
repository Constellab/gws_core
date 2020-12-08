# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import sys
import os
import json

__cdir__ = os.path.dirname(os.path.abspath(__file__))

ROOT_DIR = os.path.join(__cdir__, "../../../../")

if os.path.exists(os.path.join(ROOT_DIR, "./.gws")):
    BASE_WORKSPACE_DIR = os.path.join(ROOT_DIR, "./.gws")
else:
    BASE_WORKSPACE_DIR = os.path.join(ROOT_DIR, "./gws")

BASE_BRICK_DIR = os.path.join(BASE_WORKSPACE_DIR, "./bricks")
# BASE_LAB_DIR = os.path.join(BASE_WORKSPACE_DIR, "./labs")
BASE_EXTERN_DIR = os.path.join(BASE_WORKSPACE_DIR, "./externs")
BASE_LOG_DIR = os.path.join(BASE_WORKSPACE_DIR, "./logs")
BASE_DATA_DIR = os.path.join(BASE_WORKSPACE_DIR, "./data")

USER_WORKSPACE_DIR = os.path.join(ROOT_DIR, "./user")
USER_BRICK_DIR = os.path.join(USER_WORKSPACE_DIR, "./bricks/")
USER_LAB_DIR = os.path.join(USER_WORKSPACE_DIR, "./main/")
USER_EXTERN_DIR = os.path.join(USER_WORKSPACE_DIR, "./externs")
USER_LOG_DIR = os.path.join(USER_WORKSPACE_DIR, "./logs")
USER_DATA_DIR = os.path.join(USER_WORKSPACE_DIR, "./data")

DIR_TOKENS = dict(
    ROOT_DIR = ROOT_DIR,
    BASE_WORKSPACE_DIR = BASE_WORKSPACE_DIR,
    BASE_BRICK_DIR = BASE_BRICK_DIR,
    BASE_EXTERN_DIR = BASE_EXTERN_DIR,
    BASE_LOG_DIR = BASE_LOG_DIR,
    BASE_DATA_DIR = BASE_DATA_DIR,
    USER_WORKSPACE_DIR = USER_WORKSPACE_DIR,
    USER_BRICK_DIR = USER_BRICK_DIR,
    USER_EXTERN_DIR = USER_EXTERN_DIR,
    USER_LOG_DIR = USER_LOG_DIR,
    USER_DATA_DIR = USER_DATA_DIR
)

loaded_bricks = []

def read_brick_name(cwd):
    brick_name = None
    file_path = os.path.join(cwd,"settings.json")
    with open(file_path) as f:
        try:
            settings = json.load(f)
        except:
            raise Exception(f"Error while parsing the setting JSON file. Please check file setting file '{file_path}'")

    brick_name = settings.get("name",None)
    if brick_name is None:
        raise Exception(f"The brick name is required. Please check file setting file '{file_path}")
    
    return brick_name

def _update_json(d, u):
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = _update_json(d.get(k, {}), v)
        elif isinstance(v, list):
            d[k]= d.get(k, []) + v
        else:
            d[k] = v
    return d

def _replace_dir_tokens(path):
    for k in DIR_TOKENS:
        path = path.replace(f"${{{k}}}", DIR_TOKENS[k])

    return path

def _update_relative_static_paths(dep_cwd, dep_settings):

    for k in dep_settings:
        if k.endswith("_dir"):
            if not isinstance(dep_settings[k], str):
                raise Exception("Error while parsing setting. Parameter " + k + " must be a string")
            
            dep_settings[k] = _replace_dir_tokens(dep_settings[k])
            if dep_settings[k].startswith("."):
                dep_settings[k] = os.path.abspath(os.path.join(dep_cwd,dep_settings[k]))
    
    for k in dep_settings.get("dirs",{}):
        if not isinstance(dep_settings["dirs"][k], str):
            raise Exception("Error while parsing setting. Parameter " + k + " must be a string")
        
        dep_settings["dirs"][k] = _replace_dir_tokens(dep_settings["dirs"][k])
        if dep_settings["dirs"][k].startswith("."):
            dep_settings["dirs"][k] = os.path.abspath(os.path.join(dep_cwd,dep_settings["dirs"][k]))

    for k in dep_settings.get("app",{}).get("statics",{}):
        dep_settings["app"]["statics"][k] = _replace_dir_tokens(dep_settings["app"]["statics"][k])

        if dep_settings["app"]["statics"][k].startswith("."):
            dep_settings["app"]["statics"][k] = os.path.abspath(os.path.join(dep_cwd,dep_settings["app"]["statics"][k]))


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
    # dep_cwd = os.path.join(BASE_LAB_DIR, name)
    # if os.path.exists(dep_cwd):
    #     return dep_cwd

    dep_cwd = os.path.join(USER_LAB_DIR, name)
    if os.path.exists(dep_cwd):
        return dep_cwd
    
    return None

def _parse_settings(brick_cwd: str = None, brick_name:str = None, brick_settings_file_path:str = None):    
    if brick_name in loaded_bricks:
        return {}

    loaded_bricks.append(brick_name)

    if brick_cwd is None:
        raise Exception("Parameter brick_cwd is required")
    
    if not os.path.exists(brick_settings_file_path):
        raise Exception(f"The setting file of brick '{brick_name}' is not found. Please check file '{brick_settings_file_path}'")
        
    with open(brick_settings_file_path) as f:
        try:
            settings = json.load(f)
            if settings.get("name", None) is None:
                raise Exception(f"The name of the brick is not found. Please check file '{brick_settings_file_path}'")
        except:
            raise Exception(f"Error while parsing the setting JSON file. Please check file '{brick_settings_file_path}'")
    
    settings["extern_dirs"] = {}
    settings["dependency_dirs"] = {}

    # loads extern libs
    for dep in settings.get("externs",[]):
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
        sys.path.insert(0,dep_cwd)

    # allows loading the current brick
    settings["dependencies"].append(brick_name)

    # loads dependencies
    for dep in settings.get("dependencies",[]):
        dep_cwd = _find_brick(dep)
        
        if dep_cwd is None:
            dep_cwd = _find_lab(dep)
        
        if dep_cwd is None:
            continue

        sys.path.insert(0,dep_cwd)

        settings["dependency_dirs"][dep] = os.path.abspath(dep_cwd)
        dep_setting_file = os.path.join(dep_cwd,"./settings.json")
                                         
        dep_exist = (dep != brick_name)
        if dep_exist:
            dep_settings = _parse_settings(brick_cwd=dep_cwd, brick_name=dep, brick_settings_file_path=dep_setting_file)
            if len(dep_settings) > 0:
                dep_settings = _update_relative_static_paths(dep_cwd,dep_settings)
                settings = _update_json(settings, dep_settings)
        else:
            if len(settings) > 0:
                settings = _update_relative_static_paths(dep_cwd,settings)

    # uniquefy dependencies
    settings["dependencies"] = list(set(settings["dependencies"]))
    settings["externs"] = list(set(settings["externs"]))

    return settings
    
def parse_settings(brick_cwd: str = None):
    brick_name = read_brick_name(brick_cwd)
    brick_settings_file_path = os.path.join(brick_cwd, "settings.json")
    default_settings = {
        "type"          : "brick",
        "app_dir"       : "./",
        "app_host"      : "localhost",
        "app_port"      : 3000,
        "db_dir"        : "./",
        "db_name"       : "db.sqlite3",
        "is_test"       : False,
        "externs"       : [],
        "dependencies"  : [],
        "static_dirs"   : {},
        "__cwd__"       : brick_cwd
    }

    settings = _update_json(default_settings, _parse_settings(brick_cwd=brick_cwd, brick_name=brick_name, brick_settings_file_path=brick_settings_file_path))
    if not os.path.exists(settings.get("db_dir")):
        os.mkdir(settings.get("db_dir"))

    return settings

def load_settings(brick_cwd: str = None):
    from gws.settings import Settings
    settings = parse_settings(brick_cwd)
    Settings.init(settings)
    return settings