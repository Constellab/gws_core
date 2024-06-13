

from typing import List

from gws_core.config.config_params import ConfigParams
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.fs_node import FSNode
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.r_field.primitive_r_field import StrRField
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.resource_set.resource_list import ResourceList
from gws_core.resource.view.view_decorator import view
from gws_core.streamlit.streamlit_app_managers import StreamlitAppManager
from gws_core.streamlit.streamlit_view import StreamlitView


@resource_decorator("StreamlitResource", human_name="Streamlit App",
                    short_description="Streamlit App",
                    style=TypingStyle.material_icon("dashboard", background_color='#ff4b4b'))
class StreamlitResource(ResourceList):
    """
    Resource that contains a streamlit dashboard. See Streamlite live task to see how to generate it.
    """

    _streamlit_app_code: str = StrRField()

    def __init__(self, streamlit_app_code: str = None):
        super().__init__()
        self._streamlit_app_code = streamlit_app_code

    def get_streamlit_app_code(self) -> str:
        return self._streamlit_app_code

    def set_streamlit_code(self, streamlit_code: str) -> None:
        self._streamlit_app_code = streamlit_code

    def set_streamlit_code_path(self, streamlit_app_code_path: str) -> None:
        if not FileHelper.exists_on_os(streamlit_app_code_path):
            raise Exception(f"streamlit_app_code_path {streamlit_app_code_path} does not exist")

        # read the streamlit code from the file
        with open(streamlit_app_code_path, 'r', encoding="utf-8") as file_path:
            self._streamlit_app_code = file_path.read()

    def add_resource(self, resource: Resource,
                     create_new_resource: bool = True) -> None:
        """Add a resource to the list

        :param resource: resource to add
        :type resource: Resource
        :param create_new_resource: If true, a new resource is created when saving the resource.
                                    Otherwise it doesn't create a new resource but references it. In this case
                                    the resource must be an input of the task that created the ResourceList and the resource
                                    must have been saved before, defaults to True
        :type create_new_resource: bool, optional
        """

        if not isinstance(resource, FSNode):
            raise Exception("The resource must be a FSNode")
        return super().add_resource(resource, create_new_resource)

    @view(view_type=StreamlitView, default_view=True)
    def default_view(self, _: ConfigParams) -> StreamlitView:

        streamlit_app = StreamlitAppManager.create_or_get_app(self._model_id)
        resources: List[FSNode] = self.get_resources()
        streamlit_app.set_source_paths([resource.path for resource in resources])
        streamlit_app.set_streamlit_code(self.get_streamlit_app_code())
        url = streamlit_app.generate_app()

        # create the view
        view_ = StreamlitView(url)
        view_.set_favorite(True)
        return view_
