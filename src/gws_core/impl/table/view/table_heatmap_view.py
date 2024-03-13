

from __future__ import annotations

from typing import TYPE_CHECKING

from typing_extensions import TypedDict

from ....config.config_params import ConfigParams
from ....config.param.param_spec import DictParam
from ....resource.view.view_types import ViewSpecs, ViewType
from ...view.heatmap_view import HeatmapView
from .base_table_view import BaseTableView
from .table_selection import CellRange, Serie1d, TableSelection

if TYPE_CHECKING:
    from gws_core.impl.table.table import Table


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
        **BaseTableView._2d_axis_labels_specs
    }
    _type: ViewType = ViewType.HEATMAP

    def data_to_dict(self, params: ConfigParams) -> dict:
        serie: Serie1d = Serie1d.from_dict(params.get('serie'))

        table: Table

        if serie.y.type == 'range':

            cell_range: CellRange = serie.y.selection[0]
            # extract a dataframe from the first selection of the range, ignore the rest
            table = self._table.select_by_coords(
                from_row_id=cell_range.get_from().row,
                from_column_id=cell_range.get_from().column,
                to_row_id=cell_range.get_to().row,
                to_column_id=cell_range.get_to().column,
            )
        else:
            column_names = serie.y.selection
            table = self._table.select_by_column_names([{"name": column_names}])

        table.get_columns_info()

        view = HeatmapView()
        view.x_label = params.get_value("x_axis_label")
        view.y_label = params.get_value("y_axis_label")

        view.set_data(
            data=table.get_data(),
            rows_info=table.get_rows_info(),
            columns_info=table.get_columns_info())
        return view.data_to_dict(params)
