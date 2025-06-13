import os
import sys

import reflex as rx

# Load the gws_core library if not already loaded
if 'gws_core' not in sys.modules:

    core_lib_path = "/lab/user/bricks/gws_core/src"
    if not os.path.exists(core_lib_path):
        core_lib_path = "/lab/.sys/bricks/gws_core/src"
        if not os.path.exists(core_lib_path):
            raise Exception("Cannot find gws_core brick")
    sys.path.insert(0, core_lib_path)

    # retrieve the reflex app id to the logs context
    app_id = os.environ.get('GWS_APP_ID', 'reflex_app')

    from gws_core import LogContext, Settings, manage
    manage.AppManager.init_gws_env(
        main_setting_file_path=Settings.get_instance().get_main_settings_file_path(),
        log_level='INFO', log_context=LogContext.REFLEX, log_context_id=app_id)


config = rx.Config(
    app_name="test_reflex_2",
    plugins=[rx.plugins.TailwindV3Plugin()],
)
