#
# Core GWS manage module
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
#

import sys
import os
import json
import unittest
import argparse
import uvicorn

def parse_setting(cwd: str = None, module_name:str = None, setting_file:str = "settings.json"):
    if cwd is None:
        raise Exception("Parameter cwd is is required")
    
    if module_name is None:
        raise Exception("Parameter cwd is is required")

    if not os.path.exists(setting_file):
        raise "No setting.json file found"
    
    sys.path.append(os.path.join(cwd,"./"))         # -> load current module tests
    sys.path.append(os.path.join(cwd,"./src"))      # -> load current module sources

    with open(setting_file) as f:
        settings = json.load(f)

    # load modules
    for name in settings["modules"]:
        path = settings["modules"][name]
        sys.path.append(os.path.join(cwd,path))            # -> load module tests
        sys.path.append(os.path.join(cwd,path,"./src"))    # -> load module sources

        if not name == module_name:
            settings_tmp = parse_setting(os.path.join(path,"./settings.json"))
            settings_tmp.update(settings)
            settings = settings_tmp

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
        "modules"       : {},
        "static_dirs"       : {},
        "__cwd__"       : __cdir__
    }

    settings.update(parse_setting(cwd=__cdir__, module_name="gws", setting_file="./settings.json"))

    from gws.settings import Settings
    Settings.init(settings)

    from gws import runner
    runner.run()