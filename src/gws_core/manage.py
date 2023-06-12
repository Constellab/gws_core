# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import importlib
import os
import unittest
from copy import Error
from unittest.suite import BaseTestSuite

import click

from gws_core.core.utils.logger import Logger
from gws_core.settings_loader import SettingsLoader

from .app import App
from .core.db.db_manager_service import DbManagerService
from .core.exception.exceptions import BadRequestException
from .core.utils.logger import Logger
from .core.utils.settings import Settings
from .lab.system_service import SystemService
from .notebook.notebook import Notebook


class AppManager:

    root_cwd: str = None

    @classmethod
    def _init(cls, log_level: str, _is_experiment_process: bool = False,
              show_sql: bool = False, is_test: bool = False) -> Settings:

        log_dir = Settings.build_log_dir(is_test=is_test)
        Logger(log_dir=log_dir, level=log_level, _is_experiment_process=_is_experiment_process)

        if show_sql:
            Logger.print_sql_queries()

        # Load all brick settings and load bricks
        settings_loader = SettingsLoader(root_cwd=cls.root_cwd, is_test=is_test)
        settings_loader.load_settings()

        # Init the db
        DbManagerService.init_all_db()

        return settings_loader.settings

    @classmethod
    def start_app(cls, port: str, log_level: str, show_sql: bool) -> None:
        cls._init(log_level=log_level, show_sql=show_sql)

        Logger.info(
            f"Starting server in {('prod' if Settings.is_prod_mode() else 'dev')} mode with {Settings.get_lab_environment()} lab env.")

        # start app
        App.start(port=port)

    @classmethod
    def run_test(cls, test: str, log_level: str, show_sql: bool) -> None:
        if App.is_running:
            raise BadRequestException(
                "Cannot run tests while the Application is running.")

        settings = cls._init(log_level=log_level, show_sql=show_sql, is_test=True)

        if test in ["*", "all"]:
            test = "test*"
        tests: str = test.split(' ')
        loader = unittest.TestLoader()
        test_suite: BaseTestSuite = BaseTestSuite()

        for test_file in tests:
            tab = test_file.split("/")
            if len(tab) == 2:
                bricks = settings.get_bricks()
                brick_name = tab[0]
                test_file = tab[1]
                if brick_name not in bricks:
                    raise BadRequestException(
                        f"The brick '{brick_name}' is not found. It is maybe not loaded on this lab.")
                brick_dir = bricks[brick_name]["path"]
            else:
                test_file = tab[0]
                brick_dir = settings.get_cwd()

            test_suite.addTests(loader.discover(os.path.join(
                brick_dir, "./tests/"), pattern=test_file+".py"))

        if test_suite.countTestCases() == 0:
            raise Error(
                f"No test file with name '{test}' found. Or the file does not contain tests")

        test_runner = unittest.TextTestRunner()
        test_runner.run(test_suite)

    @classmethod
    def run_cli(cls, cli: str, log_level: str, show_sql: bool) -> None:
        cls._init(log_level=log_level, _is_experiment_process=True, show_sql=show_sql)

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

    @classmethod
    def run_notebook(cls, log_level: str) -> None:
        cls._init(log_level=log_level)
        Notebook.init_complete()

    @classmethod
    def reset_environment(cls) -> None:
        SystemService.reset_dev_envionment(check_user=False)
        Logger.info("Dev env reset successfully")
        return


def load_settings(cwd: str) -> None:
    print("/!\ manage.load_settings() is deprecated, please remove it and use manage.start_app() instead")
    start_app(cwd)


def start_app(cwd: str) -> None:
    AppManager.root_cwd = cwd
    _start_app_console()


def start_notebook(cwd: str, log_level: str = 'INFO') -> None:
    AppManager.root_cwd = cwd
    AppManager.run_notebook(log_level=log_level)


@click.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True
))
@click.pass_context
@click.option('--test', default="",
              help='The name test file to launch (regular expression). Enter "all" to launch all the tests')
@click.option('--cli', default="", help='Command to run using the command line interface')
@click.option('--runserver', is_flag=True, help='Starts the server')
@click.option('--port', default="3000", help='Server port', show_default=True)
@click.option('--log_level', default="INFO", help='Level for the logs', show_default=True)
@click.option('--show_sql', is_flag=True, help='Log sql queries in the console')
@click.option('--reset_env', is_flag=True, help='Reset environment')
def _start_app_console(ctx, test: bool, cli: str, runserver: bool,
                       port: str, log_level: str, show_sql: bool, reset_env: bool):
    if runserver:
        AppManager.start_app(port=port, log_level=log_level, show_sql=show_sql)
    elif cli:
        AppManager.run_cli(cli=cli, log_level=log_level, show_sql=show_sql)
    elif test:
        AppManager.run_test(test=test, log_level=log_level, show_sql=show_sql)
    elif reset_env:
        AppManager.reset_environment()
    else:
        Logger.error("Nothing to do. Please provide a valid command like --runserver, --test or --reset_env")
