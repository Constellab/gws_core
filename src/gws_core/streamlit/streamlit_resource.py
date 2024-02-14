# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from gws_core.config.config_params import ConfigParams
from gws_core.impl.file.fs_node import FSNode
from gws_core.resource.r_field.primitive_r_field import StrRField
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.resource_set.resource_set import ResourceSet
from gws_core.resource.view.view_decorator import view
from gws_core.streamlit.streamlit_app_managers import StreamlitAppManager
from gws_core.streamlit.streamlit_view import StreamlitView


@resource_decorator("StreamlitResource", human_name="Streamlit App", short_description="Streamlit App")
class StreamlitResource(ResourceSet):
    """
    Resource that contains a plotly figure.

    Ex :
    import plotly.express as px
    figure = px.scatter(source, x="A", y="B")
    resource = PlotlyResource(figure)
    """

    _streamlit_app_code: str = StrRField()

    def __init__(self, streamlit_app_code: str = None):
        super().__init__()
        self._streamlit_app_code = streamlit_app_code

    def get_streamlit_app_code(self) -> str:
        return self._streamlit_app_code

    def add_resource(self, resource: FSNode, unique_name: str = None, create_new_resource: bool = True) -> None:
        """Add a resource to the set
        """

        if not isinstance(resource, FSNode):
            raise Exception("The resource must be a FSNode")
        return super().add_resource(resource, unique_name, create_new_resource)

    @view(view_type=StreamlitView, default_view=True)
    def default_view(self, _: ConfigParams) -> StreamlitView:

        streamlit_app = StreamlitAppManager.create_or_get_app(self._model_id)
        resources: List[FSNode] = list(self.get_resources_as_set())
        streamlit_app.set_source_paths([resource.path for resource in resources])
        streamlit_app.set_streamlit_code(self.get_streamlit_app_code())
        url = streamlit_app.generate_app()

        # create the view
        view_ = StreamlitView(url)
        view_.set_favorite(True)
        return view_
