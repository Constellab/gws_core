# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import sys
import os
import json
import unittest
import argparse
import uvicorn

__cdir__ = os.path.dirname(os.path.abspath(__file__))

def read_module_name():
    module_name = None
    with open(os.path.join(__cdir__,"settings.json")) as f:
        try:
            settings = json.load(f)
        except:
            raise Exception("Error while parsing the settings JSON file. Please check file setting file.")

    module_name = settings.get("name",None)
    if module_name is None:
        raise Exception("The module name is required. Please check file setting file.")
    
    return module_name

def update_json(d, u):
    for k, v in u.items():
        if isinstance(v, dict):
            d[k] = update_json(d.get(k, {}), v)
        elif isinstance(v, list):
            d[k]= d.get(k, []) + v
        else:
            d[k] = v
    return d

def update_relative_static_paths(dep_rel_path, dep_settings):
    for k in dep_settings["statics"]:
        dep_settings["statics"][k] = os.path.join(dep_rel_path,dep_settings["statics"][k])
    
    if dep_settings.get("app", None) is None:
        return dep_settings["app"]

    for k in dep_settings["app"]:
        if k in ["scripts","modules","styles"]:
            length = len(dep_settings["app"][k])
            for i in range(length):
                dep_settings["app"][k][i] = os.path.join(dep_rel_path,dep_settings["app"][k][i])
    
    return dep_settings

def parse_settings(module_cwd: str = None, module_name:str = None, module_setting_file:str = "settings.json"):
    if module_cwd is None:
        raise Exception("Paremeter module_cwd is required")
    
    if module_name is None:
        raise Exception("Paremeter module_name is required")

    if not os.path.exists(module_setting_file):
        raise Exception("The setting file of module '"+module_name+"' is not found. Please check that file '"+module_setting_file+"'.")
    
    sys.path.append(os.path.join(module_cwd,"./"))         # -> load current module tests
    sys.path.append(os.path.join(module_cwd,"./src"))      # -> load current module sources

    with open(module_setting_file) as f:
        try:
            settings = json.load(f)
        except:
            raise Exception("Error while parsing the settings JSON file. Please check file.")
    
    if settings["dependencies"].get(module_name, None) is None:
        settings["dependencies"][module_name] = "./"

    # recursive load of dependencies
    for dep_name in settings["dependencies"]:
        if dep_name == ":external:":
            for dep_urls in settings["dependencies"][dep_name]:
                sys.path.append(os.path.join(module_cwd,dep_urls))    # -> load module sources
        else:
            dep_path = settings["dependencies"][dep_name]
            dep_cwd = os.path.join(module_cwd,dep_path)
            dep_setting_file = os.path.join(dep_cwd,"./settings.json")

            sys.path.append(dep_cwd)            # -> load module tests
            sys.path.append(os.path.join(dep_cwd,"./src"))    # -> load module sources

            if not dep_name == module_name:
                dep_settings = parse_settings(module_cwd=dep_cwd, module_name=dep_name, module_setting_file=dep_setting_file)
                dep_settings = update_relative_static_paths(dep_path,dep_settings)
                settings = update_json(dep_settings, settings)

    return settings

if __name__ == "__main__":
    settings = {
        "app_dir"       : "./",
        "app_host"      : "localhost",
        "app_port"      : 3000,
        "db_dir"        : "./",
        "db_name"       : "db.sqlite3",
        "is_test"       : False,
        "dependencies"  : {},
        "static_dirs"       : {},
        "__cwd__"       : __cdir__
    }

    module_name = read_module_name()
    settings = update_json(settings, parse_settings(module_cwd=__cdir__, module_name=module_name, module_setting_file="./settings.json"))

    from gws.settings import Settings
    Settings.init(settings)    

    from gws import runner
    runner.run()