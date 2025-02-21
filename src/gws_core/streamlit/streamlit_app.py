

import os
from typing import List

from gws_core.core.utils.logger import Logger
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.shell.base_env_shell import BaseEnvShell
from gws_core.impl.shell.shell_proxy import ShellProxy
from gws_core.streamlit.streamlit_dto import (StreamlitAppDTO,
                                              StreamlitConfigDTO)
from gws_core.user.current_user_service import CurrentUserService


class StreamlitApp():
    """Class to manage a streamlit app that runs inside the main streamlit app

    The path of this streamlit app code is passed to the main streamlit app as a parameter
    of the url. The main streamlit app load and run this app code.
    """

    app_id: str = None
    streamlit_code: str = None

    # for normal app, the resources are the source ids
    # for env app, the resources are the file paths
    resources: List[str] = None
    _app_config_dir: str = None

    params: dict = None

    app_folder_path: str = None

    _shell_proxy: ShellProxy = None

    _dev_mode: bool = False
    _dev_config_file: str = None

    APP_CONFIG_FILENAME = 'streamlit_config.json'
    MAIN_FILE = 'main.py'

    MAIN_APP_FILE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_streamlit_main_app')
    NORMAL_APP_MAIN_FILE = "main_streamlit_app.py"
    ENV_APP_MAIN_FILE = "main_streamlit_app_env.py"

    def __init__(self, app_id: str, shell_proxy: ShellProxy):
        self.app_id = app_id
        self.resources = []
        self._shell_proxy = shell_proxy

    def set_streamlit_code(self, streamlit_code: str) -> None:
        self.streamlit_code = streamlit_code

    def set_streamlit_folder(self, streamlit_folder_path: str) -> None:
        self.app_folder_path = streamlit_folder_path

    def set_streamlit_code_path(self, streamlit_app_code_path: str) -> None:
        if not FileHelper.exists_on_os(streamlit_app_code_path):
            raise Exception(f"streamlit_app_code_path {streamlit_app_code_path} does not exist")

        # read the streamlit code from the file
        with open(streamlit_app_code_path, 'r', encoding="utf-8") as file_path:
            self.streamlit_code = file_path.read()

    def set_input_resources(self, resources: List[str]) -> None:
        """ Set the resources of the app
        For normal app, the resources are the source ids
        For env app, the resources are the file paths

        :param resources: _description_
        :type resources: List[str]
        """
        self.resources = resources

    def set_params(self, params: dict) -> None:
        self.params = params

    def set_dev_mode(self, dev_config_file: str) -> None:
        self._dev_mode = True
        self._dev_config_file = dev_config_file

    def generate_app(self, working_dir: str) -> None:
        """
        Method to create the streamlit app code file and return the url to access the app.
        """
        # no need to generate the app if in dev mode
        if self._dev_mode:
            return
        self._app_config_dir = os.path.join(working_dir, self.app_id)

        FileHelper.create_dir_if_not_exist(self._app_config_dir)

        if self.app_folder_path is None and self.streamlit_code is None:
            raise Exception("streamlit_code or streamlit_folder must be set before starting the app")

        app_dir: str = None
        if self.app_folder_path is not None:
            app_dir = self.app_folder_path
        else:
            # write the main app code into the config dir
            main_app_path = os.path.join(self._app_config_dir, self.MAIN_FILE)
            Logger.debug("Writing streamlit app to " + main_app_path)
            with open(main_app_path, 'w', encoding="utf-8") as file_path:
                file_path.write(self.streamlit_code)

            app_dir = self._app_config_dir

        # write the streamlit config file
        config_path = os.path.join(self._app_config_dir, self.APP_CONFIG_FILENAME)
        config = StreamlitConfigDTO(
            app_dir_path=app_dir,  # store the app path
            source_ids=self.resources,
            params=self.params
        )
        with open(config_path, 'w', encoding="utf-8") as file_path:
            file_path.write(config.to_json_str())

    def get_app_full_url(self, host_url: str, token: str) -> str:
        if self._dev_mode:
            return host_url
        url = f"{host_url}?gws_token={token}&gws_app_id={self.app_id}"
        user = CurrentUserService.get_current_user()
        if user is not None:
            url += f"&gws_user_id={user.id}"
        return url

    def destroy(self) -> None:
        if self._app_config_dir is not None:
            FileHelper.delete_dir(self._app_config_dir)

    def is_normal_app(self) -> bool:
        return not isinstance(self._shell_proxy, BaseEnvShell)

    def get_env_code_hash(self) -> str:
        if isinstance(self._shell_proxy, BaseEnvShell):
            return self._shell_proxy.env_hash
        return "NORMAL"

    def get_shell_proxy(self) -> ShellProxy:
        return self._shell_proxy

    def is_dev_mode(self) -> bool:
        return self._dev_mode

    def get_dev_config_file(self) -> str:
        return self._dev_config_file

    def get_main_app_file_path(self) -> str:
        if self.is_normal_app():
            return os.path.join(self.MAIN_APP_FILE_FOLDER, self.NORMAL_APP_MAIN_FILE)
        else:
            return os.path.join(self.MAIN_APP_FILE_FOLDER, self.ENV_APP_MAIN_FILE)

    def to_dto(self, host_url: str, token: str) -> StreamlitAppDTO:
        return StreamlitAppDTO(
            resource_id=self.app_id,
            source_paths=self.resources,
            streamlit_app_config_path=self._app_config_dir,
            url=self.get_app_full_url(host_url, token)
        )
