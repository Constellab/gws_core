

import os
import unittest
from copy import Error
from typing import List
from unittest.suite import TestSuite

import plotly.express as px

from gws_core.core.utils.logger import Logger
from gws_core.lab.system_service import SystemService
from gws_core.model.typing_manager import TypingManager
from gws_core.scenario.scenario_run_service import ScenarioRunService
from gws_core.settings_loader import SettingsLoader
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User

from .app import App
from .core.db.db_manager_service import DbManagerService
from .core.exception.exceptions import BadRequestException
from .core.utils.logger import Logger
from .core.utils.settings import Settings
from .notebook.notebook import Notebook


class AppManager:

    @classmethod
    def init_gws_env(cls, main_setting_file_path: str,
                     log_level: str,
                     scenario_id: str = None,
                     show_sql: bool = False,
                     is_test: bool = False) -> Settings:

        log_dir = Settings.build_log_dir(is_test=is_test)

        logger_level = Logger.check_log_level(log_level)
        logger = Logger.build_main_logger(log_dir=log_dir, level=logger_level, scenario_id=scenario_id)
        if scenario_id:
            Logger.info(f"Logger configured for scenario process with log level: {logger.level}")
        else:
            Logger.info(f"Logger configured with log level: {logger.level}")

        if show_sql:
            Logger.print_sql_queries()

        # Load all brick settings and load bricks
        settings_loader = SettingsLoader(main_settings_file_path=main_setting_file_path,
                                         is_test=is_test)
        settings_loader.load_settings()

        # Init the db
        DbManagerService.init_all_db()

        # Init the typings
        TypingManager.init_typings()

        # Init plotly color, use the default plotly color
        # Force this init because it is overriden when importing streamlit
        px.defaults.color_discrete_sequence = px.colors.qualitative.Plotly

        return settings_loader.settings

    @classmethod
    def start_app(cls, main_setting_file_path: str,
                  port: str, log_level: str, show_sql: bool) -> None:
        cls.init_gws_env(main_setting_file_path=main_setting_file_path,
                         log_level=log_level, show_sql=show_sql)

        Logger.info(
            f"Starting server in {('prod' if Settings.is_prod_mode() else 'dev')} mode with {Settings.get_lab_environment()} lab env.")

        # start app
        App.start(port=int(port))

    @classmethod
    def run_test(cls, brick_dir: str, tests: List[str], log_level: str, show_sql: bool) -> None:
        if App.is_running:
            raise BadRequestException(
                "Cannot run tests while the Application is running.")

        if not tests:
            raise BadRequestException("Please provide a test to run.")

        settings_file = os.path.join(brick_dir, SettingsLoader.SETTINGS_JSON_FILE)

        if not os.path.exists(settings_file):
            raise BadRequestException(f"'settings.json' file not found in the brick '{brick_dir}'.")

        cls.init_gws_env(main_setting_file_path=settings_file,
                         log_level=log_level,
                         show_sql=show_sql,
                         is_test=True)

        if len(tests) == 1 and tests[0] in ["*", "all"]:
            tests = ["test*"]

        loader = unittest.TestLoader()
        test_suite = TestSuite()

        brick_test_folder = os.path.join(brick_dir, "tests")

        if not os.path.exists(brick_test_folder):
            raise Error(f"'tests' folder not found in brick '{brick_dir}'.")

        for test_file in tests:
            pattern = test_file + ".py" if not test_file.endswith(".py") else test_file
            test_suite.addTests(loader.discover(brick_test_folder, pattern=pattern))

        # check if there are any tests discovered
        if test_suite.countTestCases() == 0:
            raise Error(
                f"No tests discovered for input '{tests}' in brick '{brick_dir}'. Please verify that you provided the name of the tests file (not the path). The test file must start with 'test'.")

        test_runner = unittest.TextTestRunner()
        test_runner.run(test_suite)

    @classmethod
    def run_scenario(cls,
                     main_setting_file_path: str,
                     scenario_id: str,
                     user_id: str,
                     log_level: str,
                     show_sql: bool,
                     is_test: bool) -> None:
        cls.init_gws_env(main_setting_file_path=main_setting_file_path,
                         log_level=log_level,
                         scenario_id=scenario_id,
                         show_sql=show_sql,
                         is_test=is_test)

        # Authenticate the user
        user: User = User.get_by_id_and_check(user_id)
        CurrentUserService.set_current_user(user)

        ScenarioRunService.run_scenario_in_cli(scenario_id)

    @classmethod
    def run_process(cls,
                    main_setting_file_path: str,
                    scenario_id: str,
                    protocol_model_id: str,
                    process_instance_name: str,
                    user_id: str,
                    log_level: str,
                    show_sql: bool,
                    is_test: bool) -> None:
        cls.init_gws_env(main_setting_file_path=main_setting_file_path,
                         log_level=log_level,
                         scenario_id=scenario_id,
                         show_sql=show_sql,
                         is_test=is_test)

        # Authenticate the user
        user: User = User.get_by_id_and_check(user_id)
        CurrentUserService.set_current_user(user)

        ScenarioRunService.run_scenario_process_in_cli(scenario_id, protocol_model_id, process_instance_name)

    @classmethod
    def run_notebook(cls, main_settings_path: str, log_level: str) -> None:
        cls.init_gws_env(main_setting_file_path=main_settings_path, log_level=log_level)
        Notebook.init_complete()

    @classmethod
    def reset_environment(cls) -> None:
        # Init the db
        DbManagerService.init_all_db()
        SystemService.reset_dev_envionment(check_user=False)


def start_notebook(main_settings_path: str = "/lab/.sys/app/settings.json", log_level: str = 'INFO') -> None:
    AppManager.run_notebook(main_settings_path=main_settings_path, log_level=log_level)
