# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import plotly.graph_objs as go

from gws_core.config.config_params import ConfigParams
from gws_core.core.utils.utils import Utils
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.view.view_decorator import view

from .plotly_r_field import PlotlyRField
from .plotly_view import PlotlyView


@resource_decorator("PlotlyResource", human_name="Plotly resource",
                    short_description="Plotly resource",
                    icon="analytics")
class PlotlyResource(Resource):
    """
    Resource that contains a plotly figure.

    Ex :
    import plotly.express as px
    figure = px.scatter(source, x="A", y="B")
    resource = PlotlyResource(figure)
    """

    figure: go.Figure = PlotlyRField()

    def __init__(self, figure: go.Figure = None):
        super().__init__()
        self.figure = figure

    def get_figure(self) -> go.Figure:
        return self.figure

    @view(view_type=PlotlyView, human_name="View plot", short_description="View interactive plotly figure",
          default_view=True)
    def default_view(self, _: ConfigParams) -> PlotlyView:
        # If the json, is a json of a view
        view_ = PlotlyView(self.figure)
        view_.set_favorite(True)
        return view_

    def equals(self, other: object) -> bool:
        if not isinstance(other, PlotlyResource):
            return False

        return Utils.json_are_equals(
            PlotlyRField.figure_to_dict(self.figure),
            PlotlyRField.figure_to_dict(other.figure))
