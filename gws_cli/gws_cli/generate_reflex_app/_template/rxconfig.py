import os
import sys

import reflex as rx

# [START_AUTO_CODE]
# Code to load gws_core environment and initialize the main state.
# DO NOT MODIFY THIS CODE UNLESS YOU KNOW WHAT YOU ARE DOING.


def _load_module(module_path: str) -> None:
    if not os.path.exists(module_path):
        raise FileNotFoundError(f"Modules not found at {module_path}")

    sys.path.insert(0, module_path)


def _load_reflex_base():
    # Loading base state
    if 'gws_reflex_base' not in sys.modules:
        main_reflex_path = os.environ.get('GWS_REFLEX_MODULES_PATH',   None)
        if main_reflex_path is None:
            raise ValueError("GWS_REFLEX_MODULES_PATH environment variable is not set")

        _load_module(main_reflex_path)


def _load_reflex_main():
    # Loading main state (only for non virtual env apps)
    if 'gws_reflex_main' not in sys.modules:
        main_reflex_path = os.environ.get('GWS_REFLEX_MODULES_PATH',   None)
        if main_reflex_path is None:
            raise ValueError("GWS_REFLEX_MODULES_PATH environment variable is not set")

        _load_module(main_reflex_path)


def _load_gws_core():
    # Load the gws_core library if not already loaded
    if 'gws_core' not in sys.modules:

        gws_core_path = os.environ.get('GWS_REFLEX_GWS_CORE_PATH', None)
        if gws_core_path is None:
            raise ValueError("GWS_REFLEX_GWS_CORE_PATH environment variable is not set")

        _load_module(gws_core_path)

        # retrieve the reflex app id to the logs context
        app_id = os.environ.get('GWS_REFLEX_APP_ID', 'reflex_app')

        from gws_core import LogContext, Settings, manage
        manage.AppManager.init_gws_env(
            main_setting_file_path=Settings.get_instance().get_main_settings_file_path(),
            log_level='INFO', log_context=LogContext.REFLEX, log_context_id=app_id)


_load_reflex_base()

# load the gws_core library if not already loaded
# only if the app is not a virtual env app
is_virtual_env = os.environ.get('GWS_REFLEX_VIRTUAL_ENV', 'false').lower() == 'true'

if not is_virtual_env:
    _load_gws_core()
    _load_reflex_main()

api_url = os.environ.get('GWS_REFLEX_API_URL')
if api_url is None:
    raise ValueError("GWS_REFLEX_API_URL environment variable is not set")
# [END_AUTO_CODE]

config = rx.Config(
    app_name="{{APP_NAME}}",
    plugins=[],
    # [START_AUTO_CODE]
    api_url=api_url
    # [END_AUTO_CODE]
)
