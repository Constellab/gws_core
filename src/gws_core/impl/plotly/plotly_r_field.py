

from json import loads
from typing import Any

import plotly.graph_objs as go

from gws_core.resource.r_field.r_field import BaseRField


class PlotlyRField(BaseRField):
    """R field to serialize and deserialize plotly figures
    """

    def __init__(self):
        super().__init__()

    def deserialize(self, r_field_value: Any) -> go.Figure:
        return go.Figure(r_field_value)

    def serialize(self, r_field_value: go.Figure) -> Any:
        return PlotlyRField.figure_to_dict(r_field_value)

    @staticmethod
    def figure_to_dict(figure: go.Figure) -> dict:
        if figure is None:
            return None
        # use to_json instead of to_dict because to_dict is not serializable
        # to_json returns a string so we need to convert it to a dict
        return loads(figure.to_json())
