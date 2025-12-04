import os

from gws_core.apps.app_dto import AppType
from gws_core.apps.app_instance import AppInstance
from gws_core.core.utils.logger import Logger
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.shell.base_env_shell import BaseEnvShell


class StreamlitApp(AppInstance):
    """Class to manage a streamlit app that runs inside the main streamlit app

    The path of this streamlit app code is passed to the main streamlit app as a parameter
    of the url. The main streamlit app load and run this app code.
    """

    # Either the streamlit code is stored in attribute or in a file (most of the time)
    streamlit_code: str = None
    app_folder_path: str = None

    enable_debugger: bool = False

    MAIN_FILE = "main.py"

    MAIN_APP_FILE_FOLDER = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "_streamlit_main_app"
    )
    NORMAL_APP_MAIN_FILE = "main_streamlit_app.py"
    ENV_APP_MAIN_FILE = "main_streamlit_app_env.py"

    def set_streamlit_code(self, streamlit_code: str) -> None:
        self.streamlit_code = streamlit_code

    def set_streamlit_folder(self, streamlit_folder_path: str) -> None:
        self.app_folder_path = streamlit_folder_path

    def set_streamlit_code_path(self, streamlit_app_code_path: str) -> None:
        if not FileHelper.exists_on_os(streamlit_app_code_path):
            raise Exception(f"streamlit_app_code_path {streamlit_app_code_path} does not exist")

        # read the streamlit code from the file
        with open(streamlit_app_code_path, "r", encoding="utf-8") as file_path:
            self.streamlit_code = file_path.read()

    def generate_app(self, working_dir: str) -> None:
        """
        Method to create the streamlit app code file and return the url to access the app.
        """
        app_config_dir = self._generate_config_dir(working_dir)

        if self._dev_mode:
            self._generate_config_dev_mode()
        else:
            if self.app_folder_path is None and self.streamlit_code is None:
                raise Exception(
                    "streamlit_code or streamlit_folder must be set before starting the app"
                )

            app_dir: str = None
            if self.app_folder_path is not None:
                app_dir = self.app_folder_path
            else:
                # write the main app code into the config dir
                main_app_path = os.path.join(app_config_dir, self.MAIN_FILE)
                Logger.debug("Writing streamlit app to " + main_app_path)
                with open(main_app_path, "w", encoding="utf-8") as file_path:
                    file_path.write(self.streamlit_code)

                app_dir = app_config_dir

            self._generate_config(app_dir)

    def get_main_app_file_path(self) -> str:
        if self.is_virtual_env_app():
            return os.path.join(self.MAIN_APP_FILE_FOLDER, self.ENV_APP_MAIN_FILE)
        else:
            return os.path.join(self.MAIN_APP_FILE_FOLDER, self.NORMAL_APP_MAIN_FILE)

    def get_app_process_hash(self) -> str:
        if isinstance(self._shell_proxy, BaseEnvShell):
            return "STREAMLIT_" + self._shell_proxy.env_hash
        # all non-virtual env streamlit apps share the same process hash
        return "STREAMLIT_NORMAL"

    def get_app_type(self) -> AppType:
        """Get the type of the app."""
        return AppType.STREAMLIT

    def set_enable_debugger(self, enable_debugger: bool) -> None:
        self.enable_debugger = enable_debugger
