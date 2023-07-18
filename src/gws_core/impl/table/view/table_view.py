# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING

from ....config.config_params import ConfigParams
from ....config.param.param_spec import IntParam, StrParam
from ....resource.view.view_types import ViewSpecs, ViewType
from ...view.tabular_view import TabularView
from .base_table_view import BaseTableView

if TYPE_CHECKING:
    from ..table import Table

# class TableViewHeader(TypedDict):


class TableView(BaseTableView):
    """
    Use this view to return a section of a Table and enable pagination to retrieve other section.
    This view embed config to enable pagination.

    The view model is:
    ```
    {
        "type": "table"
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

    _type: ViewType = ViewType.TABLE
    _table: Table
    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "from_row": IntParam(default_value=1, human_name="From row"),
        "number_of_rows_per_page":
        IntParam(
            default_value=TabularView.MAX_NUMBER_OF_ROWS_PER_PAGE, max_value=TabularView.MAX_NUMBER_OF_ROWS_PER_PAGE, min_value=1,
            human_name="Number of rows per page"),
        "from_column": IntParam(default_value=1, human_name="From column", visibility=StrParam.PROTECTED_VISIBILITY),
        "number_of_columns_per_page":
        IntParam(
            default_value=TabularView.DEFAULT_NUMBER_OF_COLUMNS_PER_PAGE, max_value=TabularView.MAX_NUMBER_OF_COLUMNS_PER_PAGE, min_value=1,
            human_name="Number of columns per page", visibility=StrParam.PROTECTED_VISIBILITY),
        'replace_nan_by':
        StrParam(
            default_value="empty", allowed_values=["empty", "NaN", "-"],
            optional=True, visibility=StrParam.PROTECTED_VISIBILITY, human_name="Replace NaN by",
            short_description="Text to use to replace NaN values. Defaults to empty string"), }

    def data_to_dict(self, params: ConfigParams) -> dict:

        tabular_view = TabularView(
            self._table, from_row=params["from_row"] - 1,  # - 1 because communication uses 1-based indexing
            from_column=params["from_column"] - 1,  # - 1 because communication uses 1-based indexing
            number_of_rows_per_page=params["number_of_rows_per_page"],
            number_of_columns_per_page=params["number_of_columns_per_page"],
            replace_nan_by=params["replace_nan_by"])

        return tabular_view.data_to_dict(ConfigParams())
