import os

import plotly.express as px

from gws_core.core.utils.logger import LogContext, Logger
from gws_core.lab.system_service import SystemService
from gws_core.model.typing_manager import TypingManager
from gws_core.scenario.scenario_run_service import ScenarioRunService
from gws_core.settings_loader import SettingsLoader
from gws_core.test.test_helper import TestHelper
from gws_core.user.auth_context_loader import AuthContextLoader, DefaultAuthContextLoader
from gws_core.user.current_user_service import (
    AuthenticateUser,
    CurrentUserService,
)
from gws_core.user.user import User

from .app import App
from .core.db.db_manager_service import DbManagerService
from .core.utils.settings import Settings


class AppManager:
    gws_env_initialized: bool = False

    @classmethod
    def init_gws_env_and_db(
        cls,
        main_setting_file_path: str,
        log_level: str,
        log_context: LogContext = LogContext.MAIN,
        log_context_id: str | None = None,
        show_sql: bool = False,
        is_test: bool = False,
        auth_context_loader: AuthContextLoader | None = None,
    ) -> Settings:
        settings = cls.init_gws_env(
            main_setting_file_path=main_setting_file_path,
            log_level=log_level,
            log_context=log_context,
            log_context_id=log_context_id,
            show_sql=show_sql,
            is_test=is_test,
            auth_context_loader=auth_context_loader,
        )
        # Init the db
        DbManagerService.init_all_db(full_init=False)
        return settings

    @classmethod
    def init_gws_env(
        cls,
        main_setting_file_path: str,
        log_level: str,
        log_context: LogContext = LogContext.MAIN,
        log_context_id: str | None = None,
        show_sql: bool = False,
        is_test: bool = False,
        auth_context_loader: AuthContextLoader | None = None,
    ) -> Settings:
        if cls.gws_env_initialized:
            return Settings.get_instance()

        log_dir = Settings.build_log_dir(is_test=is_test)

        logger_level = Logger.check_log_level(log_level)
        logger = Logger.build_main_logger(
            log_dir=log_dir,
            level=logger_level,
            context=log_context,
            context_id=log_context_id,
            is_test=is_test,
        )
        if log_context == LogContext.MAIN:
            Logger.info(f"Logger configured with log level: {logger.level}")
        else:
            Logger.info(
                f"Logger configured for context {log_context} with object {log_context_id} with log level: {logger.level}"
            )

        # Initialize the CurrentUserService with the provided loader
        if auth_context_loader is None:
            auth_context_loader = DefaultAuthContextLoader()
        CurrentUserService.initialize_loader(auth_context_loader)

        if show_sql:
            Logger.print_sql_queries()

        # Load all brick settings and load bricks
        settings_loader = SettingsLoader(
            main_settings_file_path=main_setting_file_path, is_test=is_test
        )
        settings_loader.load_settings()

        # Init the typings
        TypingManager.init_typings()

        # Init plotly color, use the default plotly color
        # Force this init because it is overriden when importing streamlit
        px.defaults.color_discrete_sequence = px.colors.qualitative.Plotly

        cls.gws_env_initialized = True

        return settings_loader.settings

    @classmethod
    def start_app(
        cls, main_setting_file_path: str, port: str, log_level: str, show_sql: bool
    ) -> None:
        cls.init_gws_env(
            main_setting_file_path=main_setting_file_path,
            log_level=log_level,
            show_sql=show_sql,
            log_context=LogContext.MAIN,
        )

        Logger.info(
            f"Starting server in {('prod' if Settings.is_prod_mode() else 'dev')} mode with {Settings.get_lab_environment()} lab env."
        )

        # start app
        App.start(port=int(port))

    @classmethod
    def run_scenario(
        cls,
        main_setting_file_path: str,
        scenario_id: str,
        user_id: str,
        log_level: str,
        show_sql: bool,
        is_test: bool,
    ) -> None:
        cls.init_gws_env_and_db(
            main_setting_file_path=main_setting_file_path,
            log_level=log_level,
            show_sql=show_sql,
            is_test=is_test,
            log_context=LogContext.SCENARIO,
            log_context_id=scenario_id,
        )

        # Authenticate the user
        user: User = User.get_by_id_and_check(user_id)
        with AuthenticateUser(user):
            ScenarioRunService.run_scenario_in_cli(scenario_id)

    @classmethod
    def run_process(
        cls,
        main_setting_file_path: str,
        scenario_id: str,
        protocol_model_id: str,
        process_instance_name: str,
        user_id: str,
        log_level: str,
        show_sql: bool,
        is_test: bool,
    ) -> None:
        cls.init_gws_env_and_db(
            main_setting_file_path=main_setting_file_path,
            log_level=log_level,
            show_sql=show_sql,
            is_test=is_test,
            log_context=LogContext.SCENARIO,
            log_context_id=scenario_id,
        )

        # Authenticate the user
        user: User = User.get_by_id_and_check(user_id)
        with AuthenticateUser(user):
            ScenarioRunService.run_scenario_process_from_cli(
                scenario_id, protocol_model_id, process_instance_name
            )

    @classmethod
    def run_notebook(cls, main_settings_path: str, log_level: str) -> None:
        cls.init_gws_env(main_setting_file_path=main_settings_path, log_level=log_level)
        TestHelper.init_complete()

    @classmethod
    def reset_environment(cls) -> None:
        # Init the db
        DbManagerService.init_all_db(full_init=False)
        SystemService.reset_dev_envionment(check_user=False)


def start_notebook(main_settings_path: str | None = None, log_level: str = "INFO") -> None:
    if not main_settings_path:
        main_settings_path = os.path.join(Settings.get_system_folder(), "app", "settings.json")
    AppManager.run_notebook(main_settings_path=main_settings_path, log_level=log_level)
