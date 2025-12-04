import os
from abc import abstractmethod
from typing import Any, List

from gws_core.apps.app_config import AppConfig
from gws_core.apps.app_instance import AppInstance
from gws_core.apps.app_view import AppView
from gws_core.apps.apps_manager import AppsManager
from gws_core.config.config_params import ConfigParams
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import LoggerMessageObserver
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.folder import Folder
from gws_core.impl.file.fs_node import FSNode
from gws_core.impl.shell.base_env_shell import BaseEnvShell
from gws_core.impl.shell.shell_proxy import ShellProxy, ShellProxyDTO
from gws_core.impl.shell.shell_proxy_factory import ShellProxyFactory
from gws_core.model.typing_manager import TypingManager
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.r_field.dict_r_field import DictRField
from gws_core.resource.r_field.model_r_field import ModelRfield
from gws_core.resource.r_field.primitive_r_field import BoolRField, StrRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.resource.resource_set.resource_list_base import ResourceListBase
from gws_core.resource.resource_set.resource_set import ResourceSet
from gws_core.resource.view.view_decorator import view


@resource_decorator(
    "AppResource",
    human_name="App base",
    short_description="Base class for all apps",
    style=TypingStyle.material_icon("dashboard", background_color="#ff4b4b"),
    hide=True,
)
class AppResource(ResourceList):
    """
    Abstract class for all app resources. The resource
    store information about the appand contains a view that runs the app.
    """

    # Used when a AppConfig class was provided (with @app_decorator)
    _app_config_typing_name: str = StrRField()

    # Used when a folder path was provided
    # it contains the name of the sub resource that is a Folder containing the app code.
    # In this case, the app code is stored in the resource and cannot be modified.
    _code_folder_sub_resource_name: str = StrRField()

    _requires_authentification: bool = BoolRField(default_value=True)

    _shell_proxy: ShellProxyDTO = ModelRfield(ShellProxyDTO)

    _params: dict = DictRField()

    _app_config: AppConfig = None

    def __init__(self):
        super().__init__()

    @abstractmethod
    def get_main_app_file_name(self) -> str:
        """
        Get the main app file name that will be used to run the app.
        This file must be in the app folder.

        :return: main app file name
        :rtype: str
        """

    @abstractmethod
    def init_app_instance(
        self,
        shell_proxy: ShellProxy,
        resource_model_id: str,
        app_name: str,
        requires_authentification: bool,
    ) -> AppInstance:
        """
        Initialize the app instance with the shell proxy.
        This method is used to create the app instance that will be used to run the app.
        """

    def set_app_config(self, app_config: AppConfig) -> None:
        """
        Set the app config that will be used to generate the app.
        The AppResource stores the app config typing name to find the app config code.
        As long as the app config typing name does not change, the app config will be working.

        If the app config code is updated, the AppResource will automatically use the updated the app config code.

        :param app_config: app config object annotated with @app_decorator and with get_folder_path method
        :type app_config: AppConfig
        """
        if not isinstance(app_config, AppConfig):
            raise Exception("AppConfig must be a AppConfig instance")

        shell_proxy = app_config.get_shell_proxy()
        if not isinstance(shell_proxy, ShellProxy):
            raise Exception(
                "The app config 'get_shell_proxy' method must return a 'ShellProxy' instance"
            )

        if isinstance(shell_proxy, BaseEnvShell):
            # Installing the virtual environemnt so when the app is run, the environment is already set up.
            shell_proxy.install_env()

        folder_path = app_config.get_app_folder_path()
        self._check_folder(folder_path)

        self._app_config_typing_name = app_config.get_typing_name()

    def set_static_folder(self, app_folder_path: str) -> None:
        """
        Set the folder that contains the app code.

        This is only recommended if you want to force the version of the app in this Resource and avoid
        automatic updates. Otherwise use the set_app_config method.
        The folder is copied and stored as a sub resource of the AppResource.
        The app need to be re-generated to update the code.

        :param app_folder_path: path to the folder that contains the app code
        :type app_folder_path: str
        """
        self._check_folder(app_folder_path)

        # copy the folder into a sub resource
        tmp_dir = Settings.make_temp_dir()
        FileHelper.copy_dir_content_to_dir(app_folder_path, tmp_dir)
        stats_folder: Folder = Folder(tmp_dir)
        stats_folder.name = "AppConfig code"
        self.add_resource(stats_folder, create_new_resource=True)

        # store the name of the sub resource
        self._code_folder_sub_resource_name = "AppConfig code"

    def set_requires_authentication(self, requires_authentication: bool) -> None:
        """
        Set if the app requires the user to be authenticated.
        By default it requires authentication.

        :param requires_authentication: True if the app requires authentication
        :type requires_authentication: bool
        """
        self._requires_authentification = requires_authentication

    def _check_folder(self, folder_path: str) -> None:
        if not FileHelper.exists_on_os(folder_path) or not FileHelper.is_dir(folder_path):
            raise Exception(f"Folder '{folder_path}' does not exist or is not a folder")

        folder_name = FileHelper.get_dir_name(folder_path)
        if not folder_name.startswith("_"):
            raise Exception(
                f"App folder path must start with a underscore to avoid being loaded when the brick is loaded: {folder_path}"
            )

        # check if the main app file exists
        config_app_file_path = os.path.join(folder_path, self.get_main_app_file_name())
        if not FileHelper.exists_on_os(config_app_file_path) or not FileHelper.is_file(
            config_app_file_path
        ):
            raise Exception(
                f"Main file script file not found: {config_app_file_path}. Please make sure you have a {self.get_main_app_file_name()} file in the app folder."
            )

    def _get_app_config(self) -> AppConfig | None:
        if not self._app_config_typing_name:
            return None

        if not self._app_config:
            self._app_config = TypingManager.get_and_check_type_from_name(
                self._app_config_typing_name
            )()

        return self._app_config

    def _get_app_config_folder(self) -> str:
        app_config: AppConfig = self._get_app_config()
        folder = app_config.get_app_folder_path()
        self._check_folder(folder)
        return folder

    #################################### PARAMS ####################################

    def set_params(self, params: dict) -> None:
        """
        Set the parameters that will be passed to the app into the 'params' variable.

        :param params: parameters
        :type params: dict
        """
        self._params = params

    def get_params(self) -> dict:
        """
        Get the parameters that will be passed to the app.

        :return: parameters
        :rtype: dict
        """
        return self._params

    def set_param(self, key: str, value: Any) -> None:
        """
        Set a parameter that will be passed to the app into the 'params' variable.

        :param key: key of the parameter
        :type key: str
        :param value: value of the parameter (must be serializable to json)
        :type value: Any
        """
        if self._params is None:
            self._params = {}
        self._params[key] = value

    #################################### ENV CODE ####################################

    def set_env_shell_proxy(self, shell_proxy: BaseEnvShell) -> None:
        """
        Set the code that will be executed in the app environment.
        This code is executed before the app is loaded and can be used to load environment variables.

        :param env_code: code that will be executed
        :type env_code: str
        """
        if not isinstance(shell_proxy, BaseEnvShell):
            raise Exception("The shell proxy must be a BaseEnvShell instance")

        typing_name = shell_proxy.get_typing_name()
        if not typing_name:
            raise Exception(
                "The shell proxy must have a typing name, is it decorated with @typing_registrator ?"
            )

        self._shell_proxy = shell_proxy.to_dto()

        # Installing the virtual environemnt so when the app is run, the environment is already set up.
        shell_proxy.install_env()

    def is_virtual_env(self) -> bool:
        """
        Return True if the app is executed in a virtual environment.

        :return: True if the app is executed in a virtual environment
        :rtype: bool
        """
        return isinstance(self._get_shell_proxy(), BaseEnvShell)

    def _get_shell_proxy(self) -> ShellProxy:
        app_config = self._get_app_config()

        if app_config:
            return app_config.get_shell_proxy()

        if self._shell_proxy:
            return ShellProxyFactory.build_shell_proxy(self._shell_proxy)

        return ShellProxy()

    #################################### RESOURCES ####################################

    def add_resource(self, resource, create_new_resource=True) -> None:
        """Add a resource to the AppResource.

        :param resource: _description_
        :type resource: _type_
        :param create_new_resource: _description_, defaults to True
        :type create_new_resource: bool, optional
        :raises Exception: _description_
        :return: message if a warning is raised
        :rtype: str
        """
        if self.is_virtual_env() and not isinstance(resource, FSNode):
            raise Exception(
                "Only FSNode resources can be added to a AppResource when the app is executed in a virtual environment"
            )

        return super().add_resource(resource, create_new_resource)

    def add_multiple_resources(
        self, resources: List[Resource], message_dispatcher: MessageDispatcher = None
    ) -> None:
        """

        :param resources: _description_
        :type resources: List[Resource]
        """
        i = 1
        if message_dispatcher is None:
            message_dispatcher = MessageDispatcher()
        for resource in resources:
            if resource:
                # prevent nesting resource sets
                if isinstance(resource, ResourceListBase):
                    if isinstance(resource, ResourceSet):
                        message_dispatcher.notify_warning_message(
                            f"Flatten sub resource for resource {resource.name} ({str(i + 1)}) because it is a resource set. The order of the resources will not be kept."
                        )
                    else:
                        message_dispatcher.notify_warning_message(
                            f"Flatten sub resource for resource {resource.name} ({str(i + 1)}) because it is a resource list."
                        )
                    for sub_resource in resource.get_resources_as_set():
                        self.add_resource(sub_resource, create_new_resource=False)
                else:
                    self.add_resource(resource, create_new_resource=False)

            i += 1

    ########################### VIEW ####################################

    @view(
        view_type=AppView,
        human_name="View app",
        short_description="View the app in a web browser",
        default_view=True,
    )
    def default_view(self, _: ConfigParams) -> AppView:
        """This view generates the app and returns a AppView."""

        shell_proxy = self._get_shell_proxy()
        shell_proxy.attach_observer(LoggerMessageObserver())

        app = self.init_app_instance(
            shell_proxy, self.get_model_id(), self.get_name(), self._requires_authentification
        )

        # add the resources as input to the app
        app.set_input_resources(self.get_resources())

        # add the params
        app.set_params(self._params)

        # create the app asynchronously and return the instance ID
        result = AppsManager.create_or_get_app_async(app)

        # create the view with the app instance ID
        view_ = AppView(result)
        view_.set_favorite(True)
        view_.set_title(self.get_name())
        return view_
