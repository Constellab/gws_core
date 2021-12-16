# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pandas import DataFrame

from ....config.config_types import ConfigParams
from ....config.param_spec import BoolParam, ListParam, StrParam
from ....core.exception.exceptions import BadRequestException
from ....resource.view_types import ViewSpecs
from ...view.barplot_view import BarPlotView
from .base_table_view import BaseTableView

MAX_NUMBERS_OF_COLUMNS_PER_PAGE = 999


class TableBarPlotView(BaseTableView):
    """
    TableBarPlotView

    Class for creating bar plots using a Table.

    The view model is:
    ------------------

    ```
    {
        "type": "bar-plot-view",
        "data": {
            "x_label": str,
            "y_label": str,
            "x_tick_labels": List[str] | None,
            "series": [
                {
                    "data": {
                        "x": List[Float],
                        "y": List[Float],
                    },
                    "name": str,
                },
                ...
            ]
        }
    }
    ```
    """

    _data: DataFrame
    _specs: ViewSpecs = {
        **BaseTableView._specs,
        "column_names": ListParam(human_name="Column names", optional=True, short_description="List of columns to plot"),
        "use_regexp": BoolParam(default_value=False, human_name="Use regexp", short_description="True to use regular expression for column names; False otherwise"),
        "index_column": StrParam(human_name="Index column", optional=True, short_description="The index column used to label bar"),
        "x_label": StrParam(human_name="X-label", optional=True, visibility='protected', short_description="The x-axis label to display"),
        "y_label": StrParam(human_name="Y-label", optional=True, visibility='protected', short_description="The y-axis label to display"),
        "x_tick_labels": ListParam(human_name="X-tick-labels", optional=True, visibility='protected', short_description="The labels of x-axis ticks")
    }
    _view_helper = BarPlotView

    def to_dict(self, params: ConfigParams) -> dict:
        if not issubclass(self._view_helper, BarPlotView):
            raise BadRequestException("Invalid view helper. An subclass of BarPlotView is expected")

        data = self._data

        index_column = params.get_value("index_column")
        if index_column:
            data.index = data.loc[:, index_column].to_list()

        # select columns
        column_names = params.get_value("column_names", [])
        if not column_names:
            n = min(data.shape[1], MAX_NUMBERS_OF_COLUMNS_PER_PAGE)
            column_names = data.columns[0:n].to_list()
            #column_names = data.columns.to_list()
        else:
            if params["use_regexp"]:
                reg = "|".join(["^"+val+"$" for val in column_names])
                data = data.filter(regex=reg)
            else:
                column_names = [col for col in column_names if col in data.columns]
                data = data[column_names]

        # continue ...
        x_label = params.get_value("x_label", "")
        x_tick_labels = params.get_value("x_tick_labels", data.index.to_list())
        y_label = params.get_value("y_label", "")

        # # handle x tick labels
        # x_tick_labels = None
        # if params.value_is_set('x_tick_labels'):
        #     x_tick_label_columns: str = params.get_value("x_tick_labels")
        #     x_tick_labels = []
        #     for column in x_tick_label_columns:
        #         if column in data:
        #             x_tick_labels.extend(data[column].values.tolist())

        # replace NaN by 'NaN'
        data: DataFrame = data.fillna('')

        # create view
        view = self._view_helper()
        view.x_label = x_label
        view.y_label = y_label
        view.x_tick_labels = x_tick_labels
        for column_name in data.columns:
            y = data[column_name].values.tolist()
            x = list(range(0, len(y)))
            view.add_series(
                x=x,
                y=y,
                name=column_name
            )

        return view.to_dict(params)
