# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import importlib
import os
import unittest
from copy import Error
from unittest.suite import BaseTestSuite

from .app import App
from .core.db.db_manager_service import DbManagerService
from .core.exception.exceptions import BadRequestException
from .core.utils.logger import Logger
from .core.utils.settings import Settings
from .lab.system_service import SystemService


def call(is_prod: bool = True, test: str = "",
         cli: str = '', runserver=False, notebook=False,
         port="3000", log_level: str = None, show_sql=False, reset_env=False):

    Logger(level=log_level, _is_experiment_process=cli != '')

    if show_sql:
        Logger.print_sql_queries()

    is_test: bool = bool(test)

    settings = Settings.get_instance()
    settings.set_data("app_port", port)
    settings.set_data("id", os.getenv("LAB_ID"))
    settings.set_data("is_prod", is_prod)
    settings.set_data("is_debug", True)
    settings.set_data("is_test", is_test)

    if is_prod:
        # Deactivate any test in production mode
        settings.set_data("test", "")
        settings.set_data("is_test", False)

    if not settings.save():
        raise BadRequestException("Cannot save the settings in the database")

    # Init the db
    if is_test:
        if App.is_running:
            raise BadRequestException("Cannot run tests while the Application is running.")

    DbManagerService.init_all_db()

    if reset_env:
        SystemService.reset_dev_envionment(check_user=False)
        Logger.info("Dev env reset successfully")
        return

    if runserver:
        # start app
        App.start(port=port)
    elif cli:
        tab = cli.split(".")
        n = len(tab)
        module_name = ".".join(tab[0:n-1])
        function_name = tab[n-1]
        module = importlib.import_module(module_name)
        func = getattr(module, function_name, None)
        if func is None:
            raise BadRequestException(
                f"Please check that method {cli} is defined")
        else:
            func()
    elif test:
        if test in ["*", "all"]:
            test = "test*"
        tests: str = test.split(' ')
        loader = unittest.TestLoader()
        test_suite: BaseTestSuite = BaseTestSuite()
        for test_file in tests:
            tab = test_file.split("/")
            if len(tab) == 2:
                modules = settings.get_modules()
                brick_name = tab[0]
                test_file = tab[1]
                if brick_name not in modules:
                    raise BadRequestException(
                        f"The brick '{brick_name}' is not found. It is maybe not loaded on this lab.")
                if not modules[brick_name].get("is_brick"):
                    raise BadRequestException(
                        f"Module '{brick_name}' is not a brick. Unit testing is not allowed for external modules.")
                brick_dir = modules[brick_name]["path"]
            else:
                test_file = tab[0]
                brick_dir = settings.get_cwd()

            test_suite.addTests(loader.discover(os.path.join(brick_dir, "./tests/"), pattern=test_file+".py"))

        if test_suite.countTestCases() == 0:
            raise Error(f"No test file with name '{test}' found. Or the file does not contain tests")

        test_runner = unittest.TextTestRunner()
        test_runner.run(test_suite)
    elif notebook:
        # nothing ...
        pass
    else:
        Logger.error("No option provided on the run, did you forget '--runserver' or '--test' ?")

# TODO to remove on next version (like 1.1.0)


def run():
    print("/!\ runner.run() is deprecated, please remove it and use manage.start_app() instead")
