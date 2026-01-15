from abc import abstractmethod

from numpy import source

from gws_core.apps.app_dto import AppInstanceDTO, AppType
from gws_core.core.utils.logger import Logger
from gws_core.impl.shell.base_env_shell import BaseEnvShell
from gws_core.impl.shell.shell_proxy import ShellProxy
from gws_core.resource.resource import Resource


class AppInstance:
    resource_model_id: str
    name: str

    # for normal app, the resources are the source ids
    # for env app, the resources are the file paths
    resources: list[Resource] | None = None

    params: dict | None = None

    # If True, the user must be authenticated to access the app
    requires_authentication: bool = True

    _shell_proxy: ShellProxy

    _dev_mode: bool = False
    _dev_user_id: str | None = None

    def __init__(
        self,
        resource_model_id: str,
        name: str,
        shell_proxy: ShellProxy,
        requires_authentication: bool = True,
    ):
        self.resource_model_id = resource_model_id
        self.name = name
        self.resources = []
        self._shell_proxy = shell_proxy
        self.requires_authentication = requires_authentication

    @abstractmethod
    def get_app_type(self) -> AppType:
        """Get the type of the app."""

    def set_input_resources(self, resources: list[Resource]) -> None:
        """Set the resources of the app

        : param resources: _description_
        : type resources: List[str]
        """
        self.resources = resources

    def set_params(self, params: dict) -> None:
        self.params = params

    def set_requires_authentication(self, requires_authentication: bool) -> None:
        """Set if the app requires authentication. By default it requires authentication.
        If the app does not require authentication, the user access tokens are not used.
        In this case the system user is used to access the app.

        : param requires_authentication: True if the app requires authentication
        : type requires_authentication: bool
        """
        self.requires_authentication = requires_authentication

    def was_generated_from_resource_model_id(self, resource_model_id: str) -> bool:
        """Return true if the app was generated from the given resource model id"""
        return self.resource_model_id == resource_model_id

    def is_virtual_env_app(self) -> bool:
        return isinstance(self._shell_proxy, BaseEnvShell)

    def get_shell_proxy(self) -> ShellProxy:
        return self._shell_proxy

    def set_dev_user(self, user_id: str) -> None:
        """Set the user to be used in dev mode and return the user access token"""
        if not self._dev_mode:
            raise Exception("Cannot set dev user if the app is not in dev mode")
        self._dev_user_id = user_id

    def set_dev_mode(self) -> None:
        self._dev_mode = True

    def is_dev_mode(self) -> bool:
        return self._dev_mode

    def get_source_ids(self) -> list[str]:
        """Get the source ids of the app"""
        if not self.resources:
            return []
        source_ids = []
        for resource in self.resources:
            model_id = resource.get_model_id()
            if model_id:
                source_ids.append(model_id)
        return source_ids

    def to_dto(self) -> AppInstanceDTO:
        shell_proxy = self.get_shell_proxy()
        app_instance_dto = AppInstanceDTO(
            app_type=self.get_app_type(),
            app_resource_id=self.resource_model_id,
            name=self.name,
            env_type="",
            source_ids=self.get_source_ids(),
        )

        if isinstance(shell_proxy, BaseEnvShell):
            app_instance_dto.env_type = shell_proxy.get_env_type()
            app_instance_dto.env_file_path = shell_proxy.env_file_path
            try:
                app_instance_dto.env_file_content = shell_proxy.read_env_file()
            except Exception as e:
                Logger.error(f"[AppInstance] Error reading env file: {e}")
        else:
            app_instance_dto.env_type = "normal"

        return app_instance_dto
