import os

from gws_core.apps.app_dto import AppType
from gws_core.apps.app_instance import AppInstance
from gws_core.core.utils.logger import Logger
from gws_core.impl.file.file_helper import FileHelper


class StreamlitApp(AppInstance):
    """Class to manage a streamlit app that runs inside the main streamlit app

    The path of this streamlit app code is passed to the main streamlit app as a parameter
    of the url. The main streamlit app load and run this app code.
    """

    # Either the streamlit code is stored in attribute or in a file (most of the time)
    streamlit_code: str | None = None
    app_folder_path: str | None = None

    enable_debugger: bool = False

    MAIN_FILE = "main.py"

    def set_streamlit_code(self, streamlit_code: str) -> None:
        self.streamlit_code = streamlit_code

    def set_streamlit_folder(self, streamlit_folder_path: str) -> None:
        self.app_folder_path = streamlit_folder_path

    def set_streamlit_code_path(self, streamlit_app_code_path: str) -> None:
        if not FileHelper.exists_on_os(streamlit_app_code_path):
            raise Exception(f"streamlit_app_code_path {streamlit_app_code_path} does not exist")

        # read the streamlit code from the file
        with open(streamlit_app_code_path, encoding="utf-8") as file_path:
            self.streamlit_code = file_path.read()

    def build_code(self, app_dir: str) -> None:
        """Generate the streamlit app code if this is using streamlit_code attribute.

        :param app_dir: The directory where app files should be generated (already created)
        :type app_dir: str
        :return: The directory where the app content is located
        :rtype: str
        """
        if self.app_folder_path is not None:
            # If app folder path is already set, no need to build code
            return

        if self.streamlit_code is None:
            raise Exception("No streamlit code to build for the app")

        # Determine where the app content is located
        # Write the main app code into the app dir
        main_app_path = os.path.join(app_dir, self.MAIN_FILE)
        Logger.debug("Writing streamlit app to " + main_app_path)
        with open(main_app_path, "w", encoding="utf-8") as file_path:
            file_path.write(self.streamlit_code)

        # Store the app dir as content directory
        self.app_folder_path = app_dir

    def get_app_folder_path(self) -> str:
        """Get the app folder path where the main.py is located."""
        if self.app_folder_path is None:
            raise Exception("App folder path is not set")
        return self.app_folder_path

    def get_user_main_file_path(self) -> str:
        """Get the user's main.py file path."""
        return os.path.join(self.get_app_folder_path(), self.MAIN_FILE)

    def get_app_type(self) -> AppType:
        """Get the type of the app."""
        return AppType.STREAMLIT

    def set_enable_debugger(self, enable_debugger: bool) -> None:
        self.enable_debugger = enable_debugger
