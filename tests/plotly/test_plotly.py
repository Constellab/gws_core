# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from json import loads
from unittest import TestCase

import plotly.express as px
import plotly.graph_objs as go
from pandas import DataFrame

from gws_core.config.config_params import ConfigParams
from gws_core.core.utils.utils import Utils
from gws_core.impl.plotly.plotly_r_field import PlotlyRField
from gws_core.impl.plotly.plotly_view import PlotlyView


# test_plotly
class TestPlotly(TestCase):

    def test_plotly_r_field(self):
        dataframe = DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})

        figure = px.scatter(dataframe, x="A", y="B")

        r_field = PlotlyRField()

        serialized_figure = r_field.serialize(figure)
        self.assertIsInstance(serialized_figure, dict)

        deserialized_figure = r_field.deserialize(serialized_figure)

        self.assertIsInstance(deserialized_figure, go.Figure)
        Utils.assert_json_equals(loads(figure.to_json()), loads(deserialized_figure.to_json()))

    def test_plotly_view(self):
        dataframe = DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})

        figure = px.scatter(dataframe, x="A", y="B")

        view = PlotlyView(figure)

        view_dict = view.to_dict(ConfigParams())
        self.assertIsInstance(view_dict, dict)
        self.assertIsInstance(view_dict["data"]["data"], list)
        self.assertIsInstance(view_dict["data"]["layout"], dict)
