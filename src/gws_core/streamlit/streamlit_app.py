

import os
from typing import Dict, List, Optional

from gws_core.core.exception.exceptions.unauthorized_exception import \
    UnauthorizedException
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.string_helper import StringHelper
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.shell.base_env_shell import BaseEnvShell
from gws_core.impl.shell.shell_proxy import ShellProxy
from gws_core.streamlit.streamlit_dto import (StreamlitAppDTO,
                                              StreamlitConfigDTO)
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User


class StreamlitAppUrl(BaseModelDTO):
    host_url: str

    params: Optional[Dict[str, str]] = None

    def get_url(self) -> str:
        url = self.host_url

        if self.params is not None and len(self.params) > 0:
            params = "&".join([f"{key}={value}" for key, value in self.params.items()])
            url += f"?{params}"
        return url

    def add_param(self, key: str, value: str) -> None:
        if self.params is None:
            self.params = {}
        self.params[key] = value


class StreamlitApp():
    """Class to manage a streamlit app that runs inside the main streamlit app

    The path of this streamlit app code is passed to the main streamlit app as a parameter
    of the url. The main streamlit app load and run this app code.
    """

    app_id: str = None

    # for normal app, the resources are the source ids
    # for env app, the resources are the file paths
    resources: List[str] = None

    params: dict = None

    # Either the streamlit code is stored in attribute or in a file (most of the time)
    streamlit_code: str = None
    app_folder_path: str = None

    # If True, the user must be authenticated to access the app
    requires_authentication: bool = True

    # List of token of user that can access the app
    # This is provided if the app requires authentication
    # Key is access token, value is user id
    user_access_tokens: Dict[str, str] = None

    _app_config_dir: str = None
    _shell_proxy: ShellProxy = None

    _dev_mode: bool = False
    _dev_config_file: str = None

    APP_CONFIG_FILENAME = 'streamlit_config.json'
    MAIN_FILE = 'main.py'

    MAIN_APP_FILE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_streamlit_main_app')
    NORMAL_APP_MAIN_FILE = "main_streamlit_app.py"
    ENV_APP_MAIN_FILE = "main_streamlit_app_env.py"

    def __init__(self, app_id: str, shell_proxy: ShellProxy, requires_authentication: bool = True):
        self.app_id = app_id
        self.resources = []
        self._shell_proxy = shell_proxy
        self.user_access_tokens = {}
        self.requires_authentication = requires_authentication

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

    def set_requires_authentication(self, requires_authentication: bool) -> None:
        """ Set if the app requires authentication. By default it requires authentication.
        If the app does not require authentication, the user access tokens are not used.
        In this case the system user is used to access the app.

        :param requires_authentication: True if the app requires authentication
        :type requires_authentication: bool
        """
        self.requires_authentication = requires_authentication

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
        config = StreamlitConfigDTO(
            app_dir_path=app_dir,  # store the app path
            source_ids=self.resources,
            params=self.params,
            requires_authentication=self.requires_authentication,
            user_access_tokens={}
        )

        self._write_config_file(config)

    def _write_config_file(self, config: StreamlitConfigDTO) -> None:
        config_path = self._get_config_file_path()
        with open(config_path, 'w', encoding="utf-8") as file_path:
            file_path.write(config.to_json_str())

    def _read_config_file(self) -> StreamlitConfigDTO:
        config_path = self._get_config_file_path()
        with open(config_path, 'r', encoding="utf-8") as file_path:
            return StreamlitConfigDTO.from_json_str(file_path.read())

    def _get_config_file_path(self) -> str:
        return os.path.join(self._app_config_dir, self.APP_CONFIG_FILENAME)

    def add_user(self, user_id: str) -> str:
        """Add the user to the list of users that can access the app and return the user access token
        """

        # check if the user is already in the list
        for token, user_id in self.user_access_tokens.items():
            if user_id == user_id:
                return token

        user_access_token = StringHelper.generate_uuid() + '_' + str(DateHelper.now_utc_as_milliseconds())
        self.user_access_tokens[user_access_token] = user_id

        # store the user access token in the config file
        config = self._read_config_file()
        config.user_access_tokens = self.user_access_tokens
        self._write_config_file(config)
        return user_access_token

    def get_user_from_token(self, user_access_token: str) -> Optional[str]:
        """Get the user id from the user access token
        If the user does not exist, return None
        """
        return self.user_access_tokens.get(user_access_token, None)

    def was_generated_from_resource_model_id(self, resource_model_id: str) -> bool:
        """Return true if the app was generated from the given resource model id
        """
        return self.app_id == resource_model_id

    def get_app_full_url(self, host_url: str, token: str) -> StreamlitAppUrl:
        if self._dev_mode:
            return StreamlitAppUrl(host_url=host_url)

        params = {
            'gws_token': token,
            'gws_app_id': self.app_id
        }

        user: User = None
        if self.requires_authentication:
            user = CurrentUserService.get_current_user()
        else:
            user = User.get_and_check_sysuser()

        if not user:
            raise UnauthorizedException(
                f"The user could not be be authenticated with requires_authentication : {self.requires_authentication}")
        user_access_token = self.add_user(user.id)
        params['gws_user_access_token'] = user_access_token

        return StreamlitAppUrl(host_url=host_url, params=params)

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
            url=self.get_app_full_url(host_url, token).get_url(),
        )
