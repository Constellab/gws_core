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

sys.path.append(os.path.join("./src"))
from gws import runner
from gws.settings import Settings
from gws.manage import read_module_name, update_json, parse_settings

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

    module_name = read_module_name(__cdir__)
    settings = update_json(settings, parse_settings(module_cwd=__cdir__, module_name=module_name, module_setting_file="./settings.json"))
    Settings.init(settings)
    runner.run()