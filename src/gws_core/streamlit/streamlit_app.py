

import os
from typing import List, Union

from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.streamlit.streamlit_dto import StreamlitAppDTO
from gws_core.user.current_user_service import CurrentUserService


class StreamlitApp():
    """Class to manage a streamlit app that runs inside the main streamlit app

    The path of this streamlit app code is passed to the main streamlit app as a parameter
    of the url. The main streamlit app load and run this app code.
    """

    port: int = None
    app_id: str = None

    streamlit_code: str = None

    temp_folder: str = None
    source_paths: List[str] = None
    token: str = None

    _streamlit_app_code_path: str = None

    def __init__(self, port: int, app_id: str, token: str):
        self.port = port
        self.app_id = app_id
        self.token = token
        self.source_paths = []

    def set_streamlit_code(self, streamlit_code: str) -> None:
        self.streamlit_code = streamlit_code

    def set_streamlit_code_path(self, streamlit_app_code_path: str) -> None:
        if not FileHelper.exists_on_os(streamlit_app_code_path):
            raise Exception(f"streamlit_app_code_path {streamlit_app_code_path} does not exist")

        # read the streamlit code from the file
        with open(streamlit_app_code_path, 'r', encoding="utf-8") as file_path:
            self.streamlit_code = file_path.read()

    def add_source_path(self, source_path: Union[str, List[str]]) -> None:
        if isinstance(source_path, str):
            self.source_paths.append(source_path)
        elif isinstance(source_path, list):
            self.source_paths.extend(source_path)
        else:
            raise Exception("node_path must be a string or a list of string")

    def set_source_paths(self, source_paths: List[str]) -> None:
        self.source_paths = source_paths

    def get_app_url(self) -> str:
        return Settings.get_streamlit_host_url()

    def generate_app(self) -> str:
        """
        Method to create the streamlit app code file and return the url to access the app.
        """
        if self._streamlit_app_code_path is not None:
            return self.get_app_full_url()

        if self.streamlit_code is None:
            raise Exception("streamlit_code must be set before starting the app")

        # setting the source variable in the streamlit code
        full_code = f"""
source_paths = {self.source_paths}
{self.streamlit_code}
"""

        # write the streamlit app to a file
        self.temp_folder = Settings.make_temp_dir()
        app_code_path = os.path.join(self.temp_folder, "streamlit_app.py")
        Logger.info("Writing streamlit app to " + app_code_path)
        with open(app_code_path, 'w', encoding="utf-8") as file_path:
            file_path.write(full_code)

        self._streamlit_app_code_path = app_code_path

        # return the url to access the app using the token and the app code path
        return self.get_app_full_url()

    def get_app_full_url(self) -> str:
        return f"{self.get_app_url()}?gws_token={self.token}&gws_app_path={self._streamlit_app_code_path}&gws_user_id={CurrentUserService.get_and_check_current_user().id}"

    def clean(self) -> None:
        if self.temp_folder is not None:
            FileHelper.delete_dir(self.temp_folder)
            self.temp_folder = None

    def to_dto(self) -> StreamlitAppDTO:
        return StreamlitAppDTO(
            resource_id=self.app_id,
            source_paths=self.source_paths,
            streamlit_app_code_path=self._streamlit_app_code_path,
            url=self.get_app_full_url()
        )
