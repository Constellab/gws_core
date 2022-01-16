# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ....config.config_types import ConfigParams
from ....config.param_spec import IntParam, StrParam
from ....resource.view_types import ViewSpecs
from ...view.heatmap_view import HeatmapView
from .base_table_view import BaseTableView


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
        "data": dict
    }
    ```
    """

    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "from_row": IntParam(default_value=1, human_name="From row"),
        "number_of_rows_per_page":
        IntParam(
            default_value=HeatmapView.MAX_NUMBER_OF_ROWS_PER_PAGE, max_value=HeatmapView.MAX_NUMBER_OF_ROWS_PER_PAGE, min_value=1,
            human_name="Number of rows per page"),
        "from_column": IntParam(default_value=1, human_name="From column", visibility=StrParam.PROTECTED_VISIBILITY),
        "number_of_columns_per_page":
        IntParam(
            default_value=HeatmapView.MAX_NUMBER_OF_COLUMNS_PER_PAGE, max_value=HeatmapView.MAX_NUMBER_OF_COLUMNS_PER_PAGE, min_value=1,
            human_name="Number of columns per page", visibility=StrParam.PROTECTED_VISIBILITY)}

    def to_dict(self, params: ConfigParams) -> dict:
        data = self._table.get_data()
        helper_view = HeatmapView()
        helper_view.set_data(data=data)
        helper_view.from_row = params["from_row"]
        helper_view.number_of_rows_per_page = params["number_of_rows_per_page"]
        helper_view.from_column = params["from_column"]
        helper_view.number_of_columns_per_page = params["number_of_columns_per_page"]
        return helper_view.to_dict(params)
