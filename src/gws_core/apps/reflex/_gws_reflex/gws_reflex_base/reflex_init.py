

import os
import sys


class ReflexInit:

    @staticmethod
    def init() -> None:
        """ Initialize the Reflex environment.

        Raises:
            ValueError: If the environment variables are not set.
        """
        # load the gws_core library if not already loaded
        # only if the app is not a virtual env app
        is_virtual_env = os.environ.get('GWS_REFLEX_VIRTUAL_ENV', 'false').lower() == 'true'

        if not is_virtual_env:
            ReflexInit._load_gws_core()

    @staticmethod
    def _load_module(module_path: str) -> None:
        if not os.path.exists(module_path):
            raise FileNotFoundError(f"Modules not found at {module_path}")

        sys.path.insert(0, module_path)

    @staticmethod
    def _load_gws_core():
        # retrieve the reflex app id to the logs context
        app_id = os.environ.get('GWS_REFLEX_APP_ID', 'reflex_app')

        from gws_core import LogContext, Settings, manage
        manage.AppManager.init_gws_env_and_db(
            main_setting_file_path=Settings.get_instance().get_main_settings_file_path(),
            log_level='INFO', log_context=LogContext.REFLEX, log_context_id=app_id)
