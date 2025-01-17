

import os
from typing import List, Literal

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import \
    LoggerMessageObserver
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.shell.base_env_shell import BaseEnvShell
from gws_core.impl.shell.conda_shell_proxy import CondaShellProxy
from gws_core.impl.shell.mamba_shell_proxy import MambaShellProxy
from gws_core.impl.shell.pip_shell_proxy import PipShellProxy
from gws_core.impl.shell.shell_proxy import ShellProxy
from gws_core.streamlit.streamlit_dto import (StreamlitAppDTO,
                                              StreamlitConfigDTO)
from gws_core.user.current_user_service import CurrentUserService

StreamlitAppType = Literal['NORMAL', 'PIP_ENV', 'CONDA_ENV', 'MAMBA_ENV']


class StreamlitApp():
    """Class to manage a streamlit app that runs inside the main streamlit app

    The path of this streamlit app code is passed to the main streamlit app as a parameter
    of the url. The main streamlit app load and run this app code.
    """

    app_id: str = None
    app_type: StreamlitAppType = None

    streamlit_code: str = None
    env_code: str = None

    # for normal app, the resources are the source ids
    # for env app, the resources are the file paths
    resources: List[str] = None
    _app_config_dir: str = None

    params: dict = None

    app_folder_path: str = None
    env_file_path: str = None

    APP_CONFIG_FILENAME = 'streamlit_config.json'
    MAIN_FILE = 'main.py'

    def __init__(self, app_id: str, app_type: StreamlitAppType):
        self.app_id = app_id
        self.app_type = app_type
        self.resources = []

    def set_streamlit_code(self, streamlit_code: str) -> None:
        self.streamlit_code = streamlit_code

    def set_env_code(self, env_code: str) -> None:
        self.env_code = env_code

    def set_streamlit_folder(self, streamlit_folder_path: str) -> None:
        self.app_folder_path = streamlit_folder_path

    def set_env_file_path(self, env_file_path: str) -> None:
        self.env_file_path = env_file_path

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

    def generate_app(self, working_dir: str) -> None:
        """
        Method to create the streamlit app code file and return the url to access the app.
        """
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
        return f"{host_url}?gws_token={token}&gws_app_id={self.app_id}&gws_user_id={CurrentUserService.get_and_check_current_user().id}"

    def destroy(self) -> None:
        if self._app_config_dir is not None:
            FileHelper.delete_dir(self._app_config_dir)

    def is_normal_app(self) -> bool:
        return self.app_type == 'NORMAL'

    def get_env_code_hash(self) -> str:
        if self.is_normal_app():
            return self.app_type

        env_code: str = None
        if self.env_file_path:
            if not FileHelper.exists_on_os(self.env_file_path):
                raise Exception(f"The environment file '{self.env_file_path}' of the Streamlit app does not exist")

            with open(self.env_file_path, 'r', encoding="utf-8") as file_path:
                env_code = file_path.read()
        else:
            env_code = self.env_code

        return BaseEnvShell.hash_env_str(env_code)

    def get_shell_proxy(self) -> ShellProxy:
        message_dispatcher = MessageDispatcher()
        message_dispatcher.attach(LoggerMessageObserver())
        if self.app_type == 'NORMAL':
            return ShellProxy(message_dispatcher=message_dispatcher)

        if self.env_file_path:
            if self.app_type == 'CONDA_ENV':
                return CondaShellProxy(env_name="streamlit_env", env_file_path=self.env_file_path,
                                       message_dispatcher=message_dispatcher)
            elif self.app_type == 'MAMBA_ENV':
                return MambaShellProxy(env_name="streamlit_env", env_file_path=self.env_file_path,
                                       message_dispatcher=message_dispatcher)
            elif self.app_type == 'PIP_ENV':
                return PipShellProxy(env_name="streamlit_env", env_file_path=self.env_file_path,
                                     message_dispatcher=message_dispatcher)
        else:
            if self.app_type == 'CONDA_ENV':
                return CondaShellProxy.from_env_str(env_str=self.env_code, message_dispatcher=message_dispatcher)
            elif self.app_type == 'MAMBA_ENV':
                return MambaShellProxy.from_env_str(env_str=self.env_code, message_dispatcher=message_dispatcher)
            elif self.app_type == 'PIP_ENV':
                return PipShellProxy.from_env_str(env_str=self.env_code, message_dispatcher=message_dispatcher)

        raise Exception(f"Unknown app type: {self.app_type}")

    def to_dto(self, host_url: str, token: str) -> StreamlitAppDTO:
        return StreamlitAppDTO(
            resource_id=self.app_id,
            source_paths=self.resources,
            streamlit_app_config_path=self._app_config_dir,
            url=self.get_app_full_url(host_url, token)
        )
