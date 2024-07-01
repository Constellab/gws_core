

import os
from typing import List, Union

from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.streamlit.streamlit_dto import (StreamlitAppDTO,
                                              StreamlitConfigDTO)
from gws_core.user.current_user_service import CurrentUserService


class StreamlitApp():
    """Class to manage a streamlit app that runs inside the main streamlit app

    The path of this streamlit app code is passed to the main streamlit app as a parameter
    of the url. The main streamlit app load and run this app code.
    """

    port: int = None
    app_id: str = None

    streamlit_code: str = None

    resource_ids: List[str] = None
    token: str = None
    app_config_dir: str = None

    params: dict = None

    _streamlit_folder: str = None

    APP_CONFIG_FILENAME = 'streamlit_config.json'
    MAIN_FILE = 'main.py'

    def __init__(self, port: int, app_id: str, token: str,
                 app_dir: str):
        self.port = port
        self.app_id = app_id
        self.token = token
        self.app_config_dir = os.path.join(app_dir, app_id)
        self.resource_ids = []

    def set_streamlit_code(self, streamlit_code: str) -> None:
        self.streamlit_code = streamlit_code

    def set_streamlit_folder(self, streamlit_folder: str) -> None:
        self._streamlit_folder = streamlit_folder

    def set_streamlit_code_path(self, streamlit_app_code_path: str) -> None:
        if not FileHelper.exists_on_os(streamlit_app_code_path):
            raise Exception(f"streamlit_app_code_path {streamlit_app_code_path} does not exist")

        # read the streamlit code from the file
        with open(streamlit_app_code_path, 'r', encoding="utf-8") as file_path:
            self.streamlit_code = file_path.read()

    def add_source_path(self, source_path: Union[str, List[str]]) -> None:
        if isinstance(source_path, str):
            self.resource_ids.append(source_path)
        elif isinstance(source_path, list):
            self.resource_ids.extend(source_path)
        else:
            raise Exception("node_path must be a string or a list of string")

    def set_input_resources(self, resource_ids: List[str]) -> None:
        self.resource_ids = resource_ids

    def set_params(self, params: dict) -> None:
        self.params = params

    def get_app_url(self) -> str:
        return Settings.get_streamlit_host_url()

    def generate_app(self) -> str:
        """
        Method to create the streamlit app code file and return the url to access the app.
        """

        FileHelper.create_dir_if_not_exist(self.app_config_dir)

        if self._streamlit_folder is None and self.streamlit_code is None:
            raise Exception("streamlit_code or streamlit_folder must be set before starting the app")

        app_dir: str = None
        if self._streamlit_folder is not None:
            app_dir = self._streamlit_folder
        else:
            # write the main app code into the config dir
            main_app_path = os.path.join(self.app_config_dir, self.MAIN_FILE)
            Logger.info("Writing streamlit app to " + main_app_path)
            with open(main_app_path, 'w', encoding="utf-8") as file_path:
                file_path.write(self.streamlit_code)

            app_dir = self.app_config_dir

        # write the streamlit config file
        config_path = os.path.join(self.app_config_dir, self.APP_CONFIG_FILENAME)
        config = StreamlitConfigDTO(
            app_dir_path=app_dir,  # store the app path
            source_ids=self.resource_ids,
            params=self.params
        )
        with open(config_path, 'w', encoding="utf-8") as file_path:
            file_path.write(config.to_json_str())

        # return the url to access the app
        return self.get_app_full_url()

    def get_app_full_url(self) -> str:
        return f"{self.get_app_url()}?gws_token={self.token}&gws_app_id={self.app_id}&gws_user_id={CurrentUserService.get_and_check_current_user().id}"

    def clean(self) -> None:
        if self.app_config_dir is not None:
            FileHelper.delete_dir(self.app_config_dir)

    def to_dto(self) -> StreamlitAppDTO:
        return StreamlitAppDTO(
            resource_id=self.app_id,
            source_paths=self.resource_ids,
            streamlit_app_config_path=self.app_config_dir,
            url=self.get_app_full_url()
        )
