

import json

import plotly.graph_objs as go

from gws_core.config.config_params import ConfigParams
from gws_core.core.utils.utils import Utils
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource import Resource
from gws_core.resource.resource_decorator import resource_decorator
from gws_core.resource.view.view_decorator import view
from gws_core.user.current_user_service import CurrentUserService

from .plotly_r_field import PlotlyRField
from .plotly_view import PlotlyView


@resource_decorator("PlotlyResource", human_name="Plotly resource",
                    short_description="Plotly resource",
                    style=TypingStyle.material_icon("analytics", background_color="#496989"))
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

    def export_to_path(self, path: str):
        dict_ = self.export_to_dict()
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(dict_, file)

    def export_to_dict(self) -> dict:
        return PlotlyRField.figure_to_dict(self.figure)

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

    @classmethod
    def get_current_user_layout_colors(cls, use_secondary_background: bool = False) -> dict:
        """Method to get the layout colors of plotly figure according to the current user theme
        Ex : figure.update_layout(PlotlyResource.get_current_user_layout_colors())

        :param use_secondary_background: If true, the secondary background color (used in card) will be used, defaults to False
        :type use_secondary_background: bool, optional
        :return: _description_
        :rtype: dict
        """
        theme = CurrentUserService.get_current_user_theme()

        background_color = theme.secondary_background_color if use_secondary_background else theme.background_color
        return {
            'plot_bgcolor': background_color,
            'paper_bgcolor': background_color,
            'font': {
                'color': theme.text_color
            },
            'xaxis': {
                'gridcolor': theme.outline_color,
                'zerolinecolor': theme.outline_color,
                'linecolor': theme.outline_color
            },
            'yaxis': {
                'gridcolor': theme.outline_color,
                'zerolinecolor': theme.outline_color,
                'linecolor': theme.outline_color
            }
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'PlotlyResource':
        return PlotlyResource(PlotlyRField.figure_from_dict(data))

    @classmethod
    def from_json_file(cls, path: str) -> 'PlotlyResource':
        dict_: dict = None

        try:
            with open(path, 'r', encoding='utf-8') as file:
                dict_ = json.load(file)
        except Exception as e:
            raise Exception(f"Error while reading the json file {path}. {str(e)}")

        return PlotlyResource.from_dict(dict_)
