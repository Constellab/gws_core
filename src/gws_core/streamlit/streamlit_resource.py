

import os
from typing import Any, List, Type

from gws_core.config.config_params import ConfigParams
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import \
    LoggerMessageObserver
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
from gws_core.resource.r_field.primitive_r_field import StrRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.resource.resource_set.resource_list_base import ResourceListBase
from gws_core.resource.resource_set.resource_set import ResourceSet
from gws_core.resource.view.view_decorator import view
from gws_core.streamlit.streamlit_app import StreamlitApp
from gws_core.streamlit.streamlit_app_managers import StreamlitAppManager
from gws_core.streamlit.streamlit_dashboard import Dashboard
from gws_core.streamlit.streamlit_view import StreamlitView
from gws_core.task.task_model import TaskModel


@resource_decorator("StreamlitResource", human_name="Dashboard",
                    short_description="Streamlit dashboard app",
                    style=TypingStyle.material_icon("dashboard", background_color='#ff4b4b'))
class StreamlitResource(ResourceList):
    """
    Resource that contains a streamlit dashboard. See Streamlite agent to see how to generate it.
    """

    # Used when a dashboard class was provided (with @dashboard_decorator)
    _streamlit_dashboard_typing_name: str = StrRField()
    # Used when a folder path was provided
    _streamlit_sub_resource_folder_name: str = StrRField()
    # Used when code is passed as a string
    _streamlit_app_code: str = StrRField()

    _shell_proxy: ShellProxyDTO = ModelRfield(ShellProxyDTO)

    _params: dict = DictRField()

    _dashboard: Dashboard = None

    def __init__(self, streamlit_app_code: str = None):
        super().__init__()

        self._streamlit_app_code = streamlit_app_code
        self._shell_proxy = ShellProxy().to_dto()

    def get_streamlit_app_code(self) -> str:
        """
        Get the streamlit code.

        :return: streamlit code
        :rtype: str
        """
        return self._streamlit_app_code

    def set_streamlit_code(self, streamlit_code: str) -> None:
        """
        Set the streamlit code dynamically.
        The code is stored as a string, the dashboard need to be re-generated to update the code.

        :param streamlit_code: streamlit code
        :type streamlit_code: str
        """
        self._streamlit_app_code = streamlit_code

    def copy_streamlit_code_path(self, streamlit_app_code_path: str) -> None:
        """
        Set the streamlit code from a file path.
        The file will be read and the content will be copied as the streamlit code.
        Don't use this if you have multiple files for the streamlit app. In this case, use the set_streamlit_folder method.
        The code is stored as a string, the dashboard need to be re-generated to update the code.

        :param streamlit_app_code_path: path to the streamlit code
        :type streamlit_app_code_path: str
        :raises Exception: if the file does not exist
        """
        if not FileHelper.exists_on_os(streamlit_app_code_path):
            raise Exception(f"streamlit_app_code_path {streamlit_app_code_path} does not exist")

        # read the streamlit code from the file
        with open(streamlit_app_code_path, 'r', encoding="utf-8") as file_path:
            self._streamlit_app_code = file_path.read()

    def set_dashboard(self, dashboard: Dashboard) -> None:
        """
        Set the dashboard that will be used to generate the streamlit app.
        The Streamlit resource stores the dashboard typing name to find the dahsboard code.
        As long as the dashboard typing name does not change, the dashboard will be working.

        If the dashboard code is updated, the SteamlitResource will automatically use the updated the dashboard code.

        :param dashboard: dashboard object annotated with @dashboard_decorator and with get_folder_path method
        :type dashboard: Dashboard
        """
        if not isinstance(dashboard, Dashboard):
            raise Exception("Dashboard must be a Dashboard instance")

        if not isinstance(dashboard.get_shell_proxy(), ShellProxy):
            raise Exception("The dashboard 'get_shell_proxy' method must return a 'ShellProxy' instance")

        folder_path = dashboard.get_app_folder_path()
        self._check_folder(folder_path)

        self._streamlit_dashboard_typing_name = dashboard.get_typing_name()

    def set_streamlit_folder(self, streamlit_app_folder_path: str) -> None:
        """
        Set the folder that contains the streamlit code. The folder must contain a main.py file.

        This is only recommended if you want to force the version of the dashboard in this Resource and avoid
        automatic updates. Otherwise use the set_dashboard method.
        The folder is copied and stored as a sub resource of the StreamlitResource.
        The dashboard need to be re-generated to update the code.


        :param streamlit_folder: path to the folder that contains the streamlit code
        :type streamlit_folder: str
        """
        self._check_folder(streamlit_app_folder_path)

        # copy the folder into a sub resource
        tmp_dir = Settings.make_temp_dir()
        FileHelper.copy_dir_content_to_dir(streamlit_app_folder_path, tmp_dir)
        stats_folder: Folder = Folder(tmp_dir)
        stats_folder.name = "Dashboard code"
        self.add_resource(stats_folder, create_new_resource=True)

        # store the name of the sub resource
        self._streamlit_sub_resource_folder_name = 'Dashboard code'

    def _check_folder(self, folder_path: str) -> None:
        if not FileHelper.exists_on_os(folder_path) or not FileHelper.is_dir(folder_path):
            raise Exception(f"Folder '{folder_path}' does not exist or is not a folder")

        folder_name = FileHelper.get_dir_name(folder_path)
        if not folder_name.startswith('_'):
            raise Exception(
                f"Dashboard folder path must start with a underscore to avoid being loaded when the brick is loaded: {folder_path}")

        main_app_path = os.path.join(folder_path, StreamlitApp.MAIN_FILE)
        if not FileHelper.exists_on_os(main_app_path) or not FileHelper.is_file(main_app_path):
            raise Exception(
                f"Main python script file not found: {main_app_path}. Please make sure you have a main.py file in the app folder.")

    def _get_dashboard(self) -> Dashboard | None:
        if not self._streamlit_dashboard_typing_name:
            return None

        if not self._dashboard:
            self._dashboard = TypingManager.get_and_check_type_from_name(self._streamlit_dashboard_typing_name)()

        return self._dashboard

    def _get_dashboard_folder(self) -> str:
        dashboard: Dashboard = self._get_dashboard()
        folder = dashboard.get_app_folder_path()
        self._check_folder(folder)
        return folder

    #################################### PARAMS ####################################

    def set_params(self, params: dict) -> None:
        """
        Set the parameters that will be passed to the streamlit app into the 'params' variable.

        :param params: parameters
        :type params: dict
        """
        self._params = params

    def get_params(self) -> dict:
        """
        Get the parameters that will be passed to the streamlit app.

        :return: parameters
        :rtype: dict
        """
        return self._params

    def set_param(self, key: str, value: Any) -> None:
        """
        Set a parameter that will be passed to the streamlit app into the 'params' variable.

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
        Set the code that will be executed in the streamlit environment.
        This code is executed before the streamlit app is loaded and can be used to load environment variables.

        :param env_code: code that will be executed
        :type env_code: str
        """
        if not isinstance(shell_proxy, BaseEnvShell):
            raise Exception("The shell proxy must be a BaseEnvShell instance")

        typing_name = shell_proxy.get_typing_name()
        if not typing_name:
            raise Exception("The shell proxy must have a typing name, is it decorated with @typing_registrator ?")

        self._shell_proxy = shell_proxy.to_dto()

    def is_virtual_env(self) -> bool:
        """
        Return True if the streamlit app is executed in a virtual environment.

        :return: True if the streamlit app is executed in a virtual environment
        :rtype: bool
        """
        return isinstance(self._get_shell_proxy(), BaseEnvShell)
    #################################### RESOURCES ####################################

    def add_resource(self, resource, create_new_resource=True) -> None:
        """Add a resource to the StreamlitResource.

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
                "Only FSNode resources can be added to a StreamlitResource when the app is executed in a virtual environment")

        return super().add_resource(resource, create_new_resource)

    def add_multiple_resources(
            self, resources: List[Resource],
            message_dispatcher: MessageDispatcher = None) -> None:
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
                    if (isinstance(resource, ResourceSet)):
                        message_dispatcher.notify_warning_message(
                            f'Flatten sub resource for resource {resource.name} ({str(i + 1)}) because it is a resource set. The order of the resources will not be kept.')
                    else:
                        message_dispatcher.notify_warning_message(
                            f'Flatten sub resource for resource {resource.name} ({str(i + 1)}) because it is a resource list.')
                    for sub_resource in resource.get_resources_as_set():
                        self.add_resource(sub_resource, create_new_resource=False)
                else:
                    self.add_resource(resource, create_new_resource=False)

            i += 1

    #################################### VIEWS ####################################

    def _get_shell_proxy(self) -> ShellProxy:
        dashboard = self._get_dashboard()

        if dashboard:
            return dashboard.get_shell_proxy()

        if self._shell_proxy:
            return ShellProxyFactory.build_shell_proxy(self._shell_proxy)

        return ShellProxy()

    @view(view_type=StreamlitView, human_name="Dashboard", short_description="Dahsboard generated with streamlit", default_view=True)
    def default_view(self, _: ConfigParams) -> StreamlitView:

        shell_proxy = self._get_shell_proxy()
        shell_proxy.attach_observer(LoggerMessageObserver())
        streamlit_app = StreamlitApp(self.get_model_id(), shell_proxy)

        dashboard = self._get_dashboard()

        # Add the dashboard code
        if dashboard:
            folder_path = self._get_dashboard_folder()
            streamlit_app.set_streamlit_folder(folder_path)
        elif self._streamlit_sub_resource_folder_name is not None and len(self._streamlit_sub_resource_folder_name) > 0:
            folder: Folder = self.get_resource_by_name(self._streamlit_sub_resource_folder_name)
            streamlit_app.set_streamlit_folder(folder.path)
        elif self.get_streamlit_app_code() is not None and len(self.get_streamlit_app_code()) > 0:
            streamlit_app.set_streamlit_code(self.get_streamlit_app_code())
        else:
            raise Exception("The streamlit code must be set")

        # add the resources as input of the streamlit app
        resources: List[str] = []
        if self.is_virtual_env():
            resources = [resource.path for resource in self.get_resources() if isinstance(resource, FSNode)]
        else:
            resources = [resource.get_model_id() for resource in self.get_resources()]
        streamlit_app.set_input_resources(resources)

        # add the params
        streamlit_app.set_params(self._params)

        # create the app
        url = StreamlitAppManager.create_or_get_app(streamlit_app)

        # create the view
        view_ = StreamlitView(url)
        view_.set_favorite(True)
        view_.set_title(self.get_name_or_default())
        return view_

    @staticmethod
    def from_code_path(streamlit_app_code_path: str) -> 'StreamlitResource':
        """
        Create a StreamlitResource from a file path.
        The file will be read and the content will be set as the streamlit code.
        Don't use this if you have multiple files for the streamlit app. In this case, use the set_streamlit_folder method.

        :param streamlit_app_code_path: _description_
        :type streamlit_app_code_path: str
        :return: _description_
        :rtype: StreamlitResource
        """
        streamlit_resource = StreamlitResource()
        streamlit_resource.copy_streamlit_code_path(streamlit_app_code_path)
        return streamlit_resource

    @classmethod
    def migrate_streamlit_resources(cls, task_typing_name: str, dashboard_typing_name: str) -> None:
        """method to migrate streamlit resources to use the dashboard class

        Args:
            task_typing_name (str): typing name of the task that generated the SteamlitResource
        """
        resource_models: List[ResourceModel] = ResourceModel.select().join(
            TaskModel, on=(ResourceModel.task_model == TaskModel.id)).where(
            (ResourceModel.resource_typing_name == cls.get_typing_name()) &
            (TaskModel.process_typing_name == task_typing_name))

        for resource_model in resource_models:
            kv_store = resource_model.get_kv_store()
            _streamlit_folder = kv_store.get('_streamlit_folder')

            if _streamlit_folder:
                kv_store._lock = False
                kv_store['_streamlit_dashboard_typing_name'] = dashboard_typing_name
                del kv_store['_streamlit_folder']
                kv_store._lock = True

                resource_model.save(skip_hook=True)
