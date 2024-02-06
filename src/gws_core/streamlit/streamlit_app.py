# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from typing import List, Union

from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper


class StreamlitApp():
    """Class to manage a streamlit app that runs inside the main streamlit app

    The path of this streamlit app code is passed to the main streamlit app as a parameter
    of the url. The main streamlit app load and run this app code.
    """

    port: int = None
    resource_id: str = None

    streamlit_code: str = None
    temp_folder: str = None
    fs_node_paths: List[str] = None
    token: str = None

    _streamlit_app_code_path: str = None

    def __init__(self, port: int, resource_id: str, token: str):
        self.port = port
        self.resource_id = resource_id
        self.token = token
        self.fs_node_paths = []

    def set_streamlit_code(self, streamlit_code: str) -> None:
        self.streamlit_code = streamlit_code

    def add_fs_node_path(self, node_path: Union[str, List[str]]) -> None:
        if isinstance(node_path, str):
            self.fs_node_paths.append(node_path)
        elif isinstance(node_path, list):
            self.fs_node_paths.extend(node_path)
        else:
            raise Exception("node_path must be a string or a list of string")

    def set_fs_node_paths(self, fs_nodes: List[str]) -> None:
        self.fs_node_paths = fs_nodes

    def get_app_url(self) -> str:
        return f"http://localhost:{self.port}"

    def generate_app(self) -> str:
        """
        Method to create the streamlit app code file and return the url to access the app.
        """
        if self._streamlit_app_code_path is not None:
            return f"{self.get_app_url()}?gws_token={self.token}&gws_app_path={self._streamlit_app_code_path}"

        if self.streamlit_code is None:
            raise Exception("streamlit_code must be set before starting the app")

        # setting the source variable in the streamlit code
        full_code = f"""
source_paths = {self.fs_node_paths}
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
        return f"{self.get_app_url()}?gws_token={self.token}&gws_app_path={app_code_path}"

    def clean(self) -> None:
        if self.temp_folder is not None:
            FileHelper.delete_dir(self.temp_folder)
            self.temp_folder = None
