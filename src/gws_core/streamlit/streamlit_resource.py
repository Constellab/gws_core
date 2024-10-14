

import os
from typing import Any, List

from gws_core.config.config_params import ConfigParams
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.fs_node import FSNode
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.r_field.dict_r_field import DictRField
from gws_core.resource.r_field.primitive_r_field import StrRField
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.resource.view.view_decorator import view
from gws_core.streamlit.streamlit_app import StreamlitApp
from gws_core.streamlit.streamlit_app_managers import StreamlitAppManager
from gws_core.streamlit.streamlit_view import StreamlitView


@resource_decorator("StreamlitResource", human_name="Streamlit App",
                    short_description="Streamlit App",
                    style=TypingStyle.material_icon("dashboard", background_color='#ff4b4b'))
class StreamlitResource(ResourceList):
    """
    Resource that contains a streamlit dashboard. See Streamlite agent to see how to generate it.
    """

    _streamlit_app_code: str = StrRField()
    _streamlit_folder: str = StrRField()

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

        :param streamlit_code: streamlit code
        :type streamlit_code: str
        """
        self._streamlit_app_code = streamlit_code

    def set_streamlit_code_path(self, streamlit_app_code_path: str) -> None:
        """
        Set the streamlit code from a file path.
        The file will be read and the content will be set as the streamlit code.
        Don't use this if you have multiple files for the streamlit app. In this case, use the set_streamlit_folder method.

        :param streamlit_app_code_path: path to the streamlit code
        :type streamlit_app_code_path: str
        :raises Exception: if the file does not exist
        """
        if not FileHelper.exists_on_os(streamlit_app_code_path):
            raise Exception(f"streamlit_app_code_path {streamlit_app_code_path} does not exist")

        # read the streamlit code from the file
        with open(streamlit_app_code_path, 'r', encoding="utf-8") as file_path:
            self._streamlit_app_code = file_path.read()

    def set_streamlit_folder(self, streamlit_app_folder_path: str) -> None:
        """
        Set the folder that contains the streamlit code. The folder must contain a main.py file.

        :param streamlit_folder: path to the folder that contains the streamlit code
        :type streamlit_folder: str
        """
        if not FileHelper.exists_on_os(streamlit_app_folder_path) or not FileHelper.is_dir(streamlit_app_folder_path):
            raise Exception(f"Folder '{streamlit_app_folder_path}' does not exis or is not a folder")

        main_app_path = os.path.join(streamlit_app_folder_path, StreamlitApp.MAIN_FILE)
        if not FileHelper.exists_on_os(main_app_path) or not FileHelper.is_file(main_app_path):
            raise Exception(
                f"Main python script file not found: {main_app_path}. Please make sure you have a main.py file in the app folder.")

        self._streamlit_folder = streamlit_app_folder_path

    def get_streamlit_folder(self) -> str:
        return self._streamlit_folder

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

        if self._streamlit_folder is not None and len(self._streamlit_folder) > 0:
            streamlit_app.set_streamlit_folder(self._streamlit_folder)
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
