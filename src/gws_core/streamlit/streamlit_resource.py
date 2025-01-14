

import os
from typing import Any, List, Type

from gws_core.config.config_params import ConfigParams
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.folder import Folder
from gws_core.impl.file.fs_node import FSNode
from gws_core.model.typing_manager import TypingManager
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.r_field.dict_r_field import DictRField
from gws_core.resource.r_field.primitive_r_field import StrRField
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.resource.view.view_decorator import view
from gws_core.streamlit.streamlit_app import StreamlitApp
from gws_core.streamlit.streamlit_app_managers import StreamlitAppManager
from gws_core.streamlit.streamlit_dashboard import Dashboard
from gws_core.streamlit.streamlit_view import StreamlitView
from gws_core.task.task_model import TaskModel


@resource_decorator("StreamlitResource", human_name="Streamlit App",
                    short_description="Streamlit App",
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

    _params: dict = DictRField()

    def __init__(self, streamlit_app_code: str = None):
        super().__init__()
        self._streamlit_app_code = streamlit_app_code

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

    def set_streamlit_code_path(self, streamlit_app_code_path: str) -> None:
        """
        Set the streamlit code from a file path.
        The file will be read and the content will be set as the streamlit code.
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

        folder_path = dashboard.get_folder_path()
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

    def _get_dashboard_folder(self) -> str:
        dashboard_type: Type[Dashboard] = TypingManager.get_and_check_type_from_name(
            self._streamlit_dashboard_typing_name)
        dashboard: Dashboard = dashboard_type()
        folder = dashboard.get_folder_path()
        self._check_folder(folder)
        return folder

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

    @view(view_type=StreamlitView, human_name="Dashboard", short_description="Dahsboard generated with streamlit", default_view=True)
    def default_view(self, _: ConfigParams) -> StreamlitView:

        streamlit_app = StreamlitAppManager.create_or_get_app(self.uid)

        if self._streamlit_dashboard_typing_name is not None and len(self._streamlit_dashboard_typing_name) > 0:
            folder_path = self._get_dashboard_folder()
            streamlit_app.set_streamlit_folder(folder_path)
        elif self._streamlit_sub_resource_folder_name is not None and len(self._streamlit_sub_resource_folder_name) > 0:
            folder: Folder = self.get_resource_by_name(self._streamlit_sub_resource_folder_name)
            streamlit_app.set_streamlit_folder(folder.path)
        else:
            streamlit_app.set_streamlit_code(self.get_streamlit_app_code())

        # add the resources as input of the streamlit app
        resources: List[FSNode] = self.get_resources()
        streamlit_app.set_input_resources([resource.get_model_id() for resource in resources])

        streamlit_app.set_params(self._params)
        url = streamlit_app.generate_app()

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
        streamlit_resource.set_streamlit_code_path(streamlit_app_code_path)
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
