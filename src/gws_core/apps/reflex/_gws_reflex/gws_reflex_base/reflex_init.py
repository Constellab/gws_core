import os


class ReflexInit:
    @staticmethod
    def init() -> None:
        """Initialize the Reflex environment.

        Raises:
            ValueError: If the environment variables are not set.
        """
        # load the gws_core library if not already loaded
        # only if the app is not a virtual env app
        is_virtual_env = os.environ.get("GWS_IS_VIRTUAL_ENV", "false").lower() == "true"

        if not is_virtual_env:
            ReflexInit._load_gws_core()

    @staticmethod
    def _load_gws_core():
        # retrieve the reflex app id to the logs context
        from gws_reflex_main.reflex_auth_context_loader import ReflexAuthContextLoader

        from gws_core import LogContext, Settings, manage

        if manage.AppManager.gws_env_initialized:
            return
        app_id = os.environ.get("GWS_APP_ID", "reflex_app")

        is_test = os.environ.get("GWS_IS_TEST_ENV", "false").lower() == "true"

        # Inherit the parent process's log level (set by the CLI's --log-level and
        # forwarded via GWS_LOG_LEVEL), falling back to INFO when not provided.
        log_level = os.environ.get("GWS_LOG_LEVEL") or "INFO"

        manage.AppManager.init_gws_env_and_db(
            main_setting_file_path=Settings.get_instance().get_main_settings_file_path(),
            log_level=log_level,
            log_context=LogContext.REFLEX,
            log_context_id=app_id,
            is_test=is_test,
            auth_context_loader=ReflexAuthContextLoader(),
        )
