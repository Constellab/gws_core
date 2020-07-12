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
import collections.abc

module_name = "gws"

def update_json(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update_json(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def parse_settings(cwd: str = None, dep_name:str = None, setting_file:str = "settings.json"):
    if cwd is None:
        raise Exception("Parameter cwd is is required")
    
    if dep_name is None:
        raise Exception("Parameter cwd is is required")

    if not os.path.exists(setting_file):
        raise "No setting.json file found"
    
    sys.path.append(os.path.join(cwd,"./"))         # -> load current module tests
    sys.path.append(os.path.join(cwd,"./src"))      # -> load current module sources

    with open(setting_file) as f:
        try:
            settings = json.load(f)
        except:
            raise Exception("Error while parsing the settings JSON file. Please check file.")
    
    if settings["dependencies"].get(module_name, None) is None:
        settings["dependencies"][module_name] = "./"

    # recursive load of dependencies
    for name in settings["dependencies"]:
        path = settings["dependencies"][name]
        sys.path.append(os.path.join(cwd,path))            # -> load module tests
        sys.path.append(os.path.join(cwd,path,"./src"))    # -> load module sources

        if not name == dep_name:
            new_settings = parse_settings(os.path.join(path,"./settings.json"))
            settings = update_json(new_settings, settings)

    return settings

if __name__ == "__main__":
    __cdir__ = os.path.dirname(os.path.abspath(__file__))
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

    settings = update_json(settings, parse_settings(cwd=__cdir__, dep_name=module_name, setting_file="./settings.json"))
    
    from gws.settings import Settings
    Settings.init(settings)    

    from gws import runner
    runner.run()