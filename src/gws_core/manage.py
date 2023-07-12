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
from gws_core.experiment.experiment_run_service import ExperimentRunService
from gws_core.settings_loader import SettingsLoader
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User

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
    def _init(cls, log_level: str, experiment_id: str = None,
              show_sql: bool = False, is_test: bool = False) -> Settings:

        log_dir = Settings.build_log_dir(is_test=is_test)
        Logger(log_dir=log_dir, level=log_level, experiment_id=experiment_id)

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
    def run_experiment(cls, experiment_id: str, user_id: str, log_level: str, show_sql: bool, is_test: bool) -> None:
        cls._init(log_level=log_level, experiment_id=experiment_id, show_sql=show_sql, is_test=is_test)

        if experiment_id is None:
            raise BadRequestException("Please provide an experiment id to run the experiment")
        if user_id is None:
            raise BadRequestException("Please provide a user id to run the experiment")

        # Authenticate the user
        user: User = User.get_by_id_and_check(user_id)
        CurrentUserService.set_current_user(user)

        ExperimentRunService.run_experiment_in_cli(experiment_id)

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
@click.option('--run-experiment', is_flag=True, default=False,
              help='When set, this start a new process to run the experiment')
@click.option('--runserver', is_flag=True, help='Starts the server')
@click.option('--port', default="3000", help='Server port', show_default=True)
@click.option('--log_level', default="INFO", help='Level for the logs', show_default=True)
@click.option('--show_sql', is_flag=True, help='Log sql queries in the console')
@click.option('--reset_env', is_flag=True, help='Reset environment')
@click.option('--experiment-id', help='Experiment id')
@click.option('--user-id', help='User id')
def _start_app_console(ctx, test: str, run_experiment: bool, runserver: bool,
                       port: str, log_level: str, show_sql: bool, reset_env: bool,
                       experiment_id: str, user_id: str) -> None:
    if runserver:
        AppManager.start_app(port=port, log_level=log_level, show_sql=show_sql)
    elif run_experiment:
        AppManager.run_experiment(experiment_id=experiment_id, user_id=user_id,
                                  log_level=log_level, show_sql=show_sql, is_test=bool(test))
    elif test:
        AppManager.run_test(test=test, log_level=log_level, show_sql=show_sql)
    elif reset_env:
        AppManager.reset_environment()
    else:
        Logger.error("Nothing to do. Please provide a valid command like --runserver, --test or --reset_env")
