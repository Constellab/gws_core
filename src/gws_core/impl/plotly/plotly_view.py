# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import plotly.graph_objs as go

from gws_core.config.config_types import ConfigParams
from gws_core.impl.plotly.plotly_r_field import PlotlyRField
from gws_core.resource.view.view import View
from gws_core.resource.view.view_types import ViewType


class PlotlyView(View):
    """View to generate a plotly figure.
    It takes a plotly figure as input, example :

    import plotly.express as px
    figure = px.scatter(dataframe, x='x', y='y').
    view = PlotlyView(figure)

    :param View: _description_
    :type View: _type_
      "type": "plotly-view",
      "title": str,
      "caption": str,
      "data": {
        'data': Any[],
        'layout': dict,
      }
    """

    figure: go.Figure = None

    _type: ViewType = ViewType.PLOTLY

    def __init__(self, figure: go.Figure):
        super().__init__()
        self.figure = figure

    def data_to_dict(self, params: ConfigParams) -> dict:
        # convert the figure to json
        # the to_dict was not serializable
        return PlotlyRField.figure_to_dict(self.figure)
