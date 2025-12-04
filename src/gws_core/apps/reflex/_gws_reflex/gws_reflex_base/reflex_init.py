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
        is_virtual_env = os.environ.get("GWS_REFLEX_VIRTUAL_ENV", "false").lower() == "true"

        if not is_virtual_env:
            ReflexInit._load_gws_core()

    @staticmethod
    def _load_gws_core():
        # retrieve the reflex app id to the logs context
        from gws_core import LogContext, Settings, manage

        if manage.AppManager.gws_env_initialized:
            return
        app_id = os.environ.get("GWS_REFLEX_APP_ID", "reflex_app")

        is_test = os.environ.get("GWS_REFLEX_TEST_ENV", "false").lower() == "true"

        manage.AppManager.init_gws_env_and_db(
            main_setting_file_path=Settings.get_instance().get_main_settings_file_path(),
            log_level="INFO",
            log_context=LogContext.REFLEX,
            log_context_id=app_id,
            is_test=is_test,
        )
