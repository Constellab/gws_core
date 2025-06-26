

import os
import sys

from gws_core.apps.app_instance import AppInstance
from gws_core.apps.app_process import AppProcess
from gws_core.apps.reflex.reflex_app import ReflexApp
from gws_core.core.model.sys_proc import SysProc
from gws_core.core.service.external_api_service import ExternalApiService
from gws_core.core.utils.logger import Logger


class ReflexProcess(AppProcess):
    """Object representing a running Reflex app process.
    This process runs the front and back of a Reflex app.
    It runs the command:
    reflex run
    """

    front_port: int = None
    back_port: int = None

    back_host_url: str = None

    # timeout in second to wait for the main app to start
    # increase it to 60 to allow the app to start as it compiles the front and back
    START_APP_TIMEOUT = 60

    REFLEX_MODULES_PATH = "_gws_reflex"

    def __init__(self, front_port: int, front_host_url: str,
                 back_port: int, back_host_url: str,
                 env_hash: str = None):
        super().__init__(front_host_url, env_hash)
        self.front_port = front_port
        self.back_port = back_port
        self.back_host_url = back_host_url

    def _start_process(self, app: AppInstance) -> SysProc:
        if not isinstance(app, ReflexApp):
            raise Exception("The app must be a ReflexApp instance")
        Logger.debug(f"Starting reflex process for front port {self.front_port} and back port {self.back_port}")

        cmd = ['reflex', 'run',
               f'--frontend-port={self.front_port}',
               f'--backend-port={self.back_port}',
               ]

        shell_proxy = app.get_and_check_shell_proxy()

        # force the shell proxy working directory to the app directory
        # because the reflex command must be run in the app directory
        shell_proxy.working_dir = app.get_app_folder()

        # Get the absolute path of the main_reflex file from module
        reflex_modules_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            ReflexProcess.REFLEX_MODULES_PATH
        )
        if not os.path.exists(reflex_modules_path):
            raise Exception(f"Reflex modules not found at {reflex_modules_path}")

        # retrieve the path of gws_core module from system path
        gws_core_path = os.path.dirname(sys.modules['gws_core'].__path__[0])

        env = {
            'GWS_REFLEX_APP_ID': app.app_id,
            'GWS_REFLEX_MODULES_PATH': reflex_modules_path,
            'GWS_REFLEX_VIRTUAL_ENV': str(app.is_virtual_env_app()),
            'GWS_REFLEX_GWS_CORE_PATH': gws_core_path,
            'GWS_REFLEX_API_URL': self.back_host_url,
        }

        if app.is_dev_mode():
            env['GWS_REFLEX_DEV_MODE'] = 'true'
            env['GWS_REFLEX_APP_CONFIG_FILE_PATH'] = app.get_dev_config_file()
        else:
            env['GWS_REFLEX_TOKEN'] = self._token
            env['GWS_REFLEX_APP_CONFIG_FILE_PATH'] = app.get_config_file_path()

        # Must use the shell_mode=False to retrieve the correct pid to check the number of connections
        return shell_proxy.run_in_new_thread(cmd, shell_mode=False, env=env)

    def call_health_check(self) -> bool:
        # health check for both front and back
        try:
            ExternalApiService.get(f"http://localhost:{self.back_port}/ping",
                                   raise_exception_if_error=True)
        except Exception:
            return False

        try:
            ExternalApiService.get(f"http://localhost:{self.front_port}",
                                   raise_exception_if_error=True)
        except Exception:
            return False

        return True

    def uses_port(self, port: int) -> bool:
        """Check if the process uses the given port"""
        return self.front_port == port or self.back_port == port
