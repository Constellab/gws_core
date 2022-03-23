# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import TypedDict

from pandas import DataFrame

from ....config.config_types import ConfigParams
from ....config.param_spec import DictParam, IntParam, StrParam
from ....resource.view_types import ViewSpecs
from ...view.heatmap_view import HeatmapView
from .base_table_view import BaseTableView, TableSelection


class HeatMapSerie(TypedDict):
    name: str
    y: TableSelection


class TableHeatmapView(BaseTableView):
    """
    TableHeatmapView

    Class for creating heatmaps using a Table.

    The view model is:
    ------------------

    ```
    {
        "type": "heatmap-view",
        "title": str,
        "caption": str,
        "data" List[List[float]],
        "rows": List[Dict["name": str, tags: Dict[str, str]]],
        "columns": List[Dict["name": str, tags: Dict[str, str]]],
        "from_row": int,
        "number_of_rows_per_page": int,
        "from_column": int,
        "number_of_columns_per_page": int,
        "total_number_of_rows": int,
        "total_number_of_columns": int,
    }
    ```
    """

    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "serie": DictParam(default_value={}),
    }

    def to_dict(self, params: ConfigParams) -> dict:
        serie: HeatMapSerie = params.get('serie')

        dataframe: DataFrame

        if serie["y"]["type"] == 'range':
            # extract a dataframe from the first selection of the range, ignore the rest
            dataframe = self.get_dataframe_from_coords(serie["y"]["selection"][0])
        else:
            dataframe = self.get_dataframe_from_columns(serie["y"]["selection"])

        row_tags = self._table.get_row_tags(none_if_empty=True)
        column_tags = self._table.get_column_tags(none_if_empty=True)
        helper_view = HeatmapView()
        helper_view.set_data(data=dataframe, row_tags=row_tags, column_tags=column_tags)
        return helper_view.to_dict(params)
