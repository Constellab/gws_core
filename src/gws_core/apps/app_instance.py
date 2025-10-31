

import json
import os
from abc import abstractmethod
from typing import Dict, List, Optional

from gws_core.apps.app_dto import (AppInstanceConfigDTO, AppInstanceDTO,
                                   AppInstanceUrl, AppType)
from gws_core.core.exception.exceptions.unauthorized_exception import \
    UnauthorizedException
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.string_helper import StringHelper
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.fs_node import FSNode
from gws_core.impl.shell.base_env_shell import BaseEnvShell
from gws_core.impl.shell.shell_proxy import ShellProxy
from gws_core.resource.resource import Resource
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User


class AppInstance():

    resource_model_id: str = None
    name: str = None

    # for normal app, the resources are the source ids
    # for env app, the resources are the file paths
    resources: List[Resource] = None

    params: dict = None

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
    _dev_user_id: str = None

    APP_CONFIG_FILENAME = 'app_config.json'
    DEV_MODE_USER_ACCESS_TOKEN_KEY = 'dev_mode_token'
    DEV_MODE_APP_ID = '1'

    def __init__(self, resource_model_id: str,
                 name: str,
                 shell_proxy: ShellProxy,
                 requires_authentication: bool = True):
        self.resource_model_id = resource_model_id
        self.name = name
        self.resources = []
        self._shell_proxy = shell_proxy
        self.user_access_tokens = {}
        self.requires_authentication = requires_authentication

    @abstractmethod
    def generate_app(self,  working_dir: str) -> None:
        pass

    @abstractmethod
    def get_app_process_hash(self) -> str:
        """Get the hash of the app process.
        If 2 hash are equal, the app will be running the in the same process.
        This is used to avoid running the same app in multiple processes.

        :return: _description_
        :rtype: str
        """

    @abstractmethod
    def get_app_type(self) -> AppType:
        """Get the type of the app."""

    def set_input_resources(self, resources: List[Resource]) -> None:
        """ Set the resources of the app

        : param resources: _description_
        : type resources: List[str]
        """
        self.resources = resources

    def set_params(self, params: dict) -> None:
        self.params = params

    def set_requires_authentication(self, requires_authentication: bool) -> None:
        """ Set if the app requires authentication. By default it requires authentication.
        If the app does not require authentication, the user access tokens are not used.
        In this case the system user is used to access the app.

        : param requires_authentication: True if the app requires authentication
        : type requires_authentication: bool
        """
        self.requires_authentication = requires_authentication

    def get_user_from_token(self, user_access_token: str) -> Optional[str]:
        """Get the user id from the user access token
        If the user does not exist, return None
        """
        return self.user_access_tokens.get(user_access_token, None)

    def was_generated_from_resource_model_id(self, resource_model_id: str) -> bool:
        """Return true if the app was generated from the given resource model id
        """
        return self.resource_model_id == resource_model_id

    def is_virtual_env_app(self) -> bool:
        return isinstance(self._shell_proxy, BaseEnvShell)

    def get_shell_proxy(self) -> ShellProxy:
        return self._shell_proxy

    def _add_user(self, user_id: str, user_access_token: str = None) -> str:
        """Add the user to the list of users that can access the app and return the user access token
        """

        # check if the user is already in the list
        for token, user_access_id in self.user_access_tokens.items():
            if user_id == user_access_id:
                return token

        if not user_access_token:
            user_access_token = StringHelper.generate_uuid() + '_' + str(DateHelper.now_utc_as_milliseconds())
        self.user_access_tokens[user_access_token] = user_id

        # store the user access token in the config file
        config = self._read_config_file()
        config.user_access_tokens = self.user_access_tokens
        self._write_config_file(config)
        return user_access_token

    def set_dev_user(self, user_id: str) -> str:
        """Set the user to be used in dev mode and return the user access token
        """
        if not self._dev_mode:
            raise Exception("Cannot set dev user if the app is not in dev mode")
        self._dev_user_id = user_id

    def get_app_full_url(self, host_url: str, token: str) -> AppInstanceUrl:
        if self._dev_mode:
            if self._dev_user_id:
                # add the dev user to the list of users that can access the app
                self._add_user(self._dev_user_id, self.DEV_MODE_USER_ACCESS_TOKEN_KEY)
            else:
                # add the system user to the list of users that can access the app
                # in dev mode, we authenticate the system user
                self._add_user(User.get_and_check_sysuser().id, self.DEV_MODE_USER_ACCESS_TOKEN_KEY)
            return AppInstanceUrl(host_url=host_url)

        params = {
            'gws_token': token,
            'gws_app_id': self.resource_model_id
        }

        user: User = None
        if self.requires_authentication:
            user = CurrentUserService.get_current_user()
        else:
            user = User.get_and_check_sysuser()

        if not user:
            raise UnauthorizedException(
                f"The user could not be be authenticated with requires_authentication : {self.requires_authentication}")
        user_access_token = self._add_user(user.id)
        params['gws_user_access_token'] = user_access_token

        return AppInstanceUrl(host_url=host_url, params=params)

    def set_dev_mode(self, dev_config_file: str) -> None:
        self._dev_mode = True
        self._dev_config_file = dev_config_file

    def is_dev_mode(self) -> bool:
        return self._dev_mode

    def destroy(self) -> None:
        if self._app_config_dir is not None:
            FileHelper.delete_dir(self._app_config_dir)

    def to_dto(self) -> AppInstanceDTO:
        shell_proxy = self.get_shell_proxy()
        app_instance_dto = AppInstanceDTO(
            app_type=self.get_app_type(),
            app_resource_id=self.resource_model_id,
            name=self.name,
            app_config_path=self.get_config_file_path(),
            env_type='',
            source_ids=[resource.get_model_id() for resource in self.resources],
        )

        if isinstance(shell_proxy, BaseEnvShell):
            app_instance_dto.env_type = shell_proxy.get_env_type()
            app_instance_dto.env_file_path = shell_proxy.env_file_path
            try:
                app_instance_dto.env_file_content = shell_proxy.read_env_file()
            except Exception as e:
                Logger.error(f"[AppInstance] Error reading env file: {e}")
        else:
            app_instance_dto.env_type = 'normal'

        return app_instance_dto

    ##################### CONFIG FILE #####################

    def _generate_config(self, app_dir: str) -> None:
        # add the resources as input to the app
        str_resources: List[str] = []
        if self.is_virtual_env_app():
            # for virtual env app, the resources are the file paths
            str_resources = [resource.path for resource in self.resources if isinstance(resource, FSNode)]
        else:
            # for normal app, the resources are the model ids
            str_resources = [resource.get_model_id() for resource in self.resources]

        # write the streamlit config file
        config = AppInstanceConfigDTO(
            app_dir_path=app_dir,  # store the app path
            source_ids=str_resources,
            params=self.params,
            requires_authentication=self.requires_authentication,
            user_access_tokens={}
        )

        self._write_config_file(config)

    def _generate_config_dev_mode(self) -> None:
        """ Generate the config dir and file from dev config file

        """
        dev_config_dict: dict = None

        with open(self._dev_config_file, 'r', encoding="utf-8") as file_path:
            dev_config_dict = json.load(file_path)

        # Making the app dir path relative to the dev config file
        app_dir_path = dev_config_dict.get('app_dir_path', '')
        if not os.path.isabs(app_dir_path):
            # make the path absolute relative to the dev config file
            dev_config_dir = os.path.dirname(self._dev_config_file)
            app_dir_path = os.path.join(dev_config_dir, app_dir_path)

        # write the streamlit config file
        config = AppInstanceConfigDTO(
            app_dir_path=app_dir_path,
            source_ids=dev_config_dict.get('source_ids', []),
            params=dev_config_dict.get('params', {}),
            requires_authentication=dev_config_dict.get('requires_authentication', False),
            user_access_tokens=dev_config_dict.get('user_access_tokens', {})
        )

        self._write_config_file(config)

    def _generate_config_dir(self, working_dir: str) -> str:
        """Generate the app config directory where the config file will be stored
        """
        self._app_config_dir = os.path.join(working_dir, self.resource_model_id)
        FileHelper.create_dir_if_not_exist(self._app_config_dir)

        return self._app_config_dir

    def _write_config_file(self, config: AppInstanceConfigDTO) -> None:
        config_path = self.get_config_file_path()
        with open(config_path, 'w', encoding="utf-8") as file_path:
            file_path.write(config.to_json_str())

    def _read_config_file(self) -> AppInstanceConfigDTO:
        config_path = self.get_config_file_path()
        with open(config_path, 'r', encoding="utf-8") as file_path:
            return AppInstanceConfigDTO.from_json_str(file_path.read())

    def get_config_file_path(self) -> str:
        return os.path.join(self._app_config_dir, self.APP_CONFIG_FILENAME)
