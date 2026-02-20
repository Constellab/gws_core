import importlib.util
import os
import sys
from datetime import datetime

import typer


class LocalLogger:
    @classmethod
    def info(cls, msg: str):
        cls._log(msg, "INFO")

    @classmethod
    def error(cls, msg):
        cls._log(msg, "ERROR")

    @classmethod
    def _log(cls, msg: str, type_: str):
        # get the date in UTC format
        typer.echo(f"{type_} - {datetime.now().isoformat()} - {msg}")


gws_core_package = "gws_core"
user_bricks_folder = os.path.join("/lab", "user", "bricks")
sys_bricks_folder = os.path.join("/lab", ".sys", "bricks")


def load_gws_core():
    # if the gws_core package is already listed in the modules, do nothing
    if gws_core_package in sys.modules:
        LocalLogger.info(f"{gws_core_package} already in sys.modules")

    # try to install in from the pip package
    elif (spec := importlib.util.find_spec(gws_core_package)) is not None:
        # If you choose to perform the actual import ...
        module = importlib.util.module_from_spec(spec)
        sys.modules[gws_core_package] = module
        spec.loader.exec_module(module)
        LocalLogger.info(f"{gws_core_package} has been imported from pip packages")

    # try to install it from the bricks folder
    else:
        core_lib_path = os.path.join(user_bricks_folder, "gws_core", "src")
        if not os.path.exists(core_lib_path):
            core_lib_path = os.path.join(sys_bricks_folder, "gws_core", "src")
            if not os.path.exists(core_lib_path):
                raise Exception("Cannot find gws_core brick")
        sys.path.insert(0, core_lib_path)
        LocalLogger.info(f"{gws_core_package} has been imported from path '{core_lib_path}'")


# if __name__ == "__main__":
#     from gws_core import manage
#     __cdir__ = os.path.dirname(os.path.abspath(__file__))
#     manage.start_app(__cdir__)
