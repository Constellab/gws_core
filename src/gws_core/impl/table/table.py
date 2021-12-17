# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List, Union

import numpy as np
from pandas import DataFrame

from ...config.config_types import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator
from ...resource.view_decorator import view
from .data_frame_r_field import DataFrameRField
from .view.barplot_view import TableBarPlotView
from .view.boxplot_view import TableBoxPlotView
from .view.heatmap_view import HeatmapView
from .view.histogram_view import TableHistogramView
from .view.lineplot_2d_view import TableLinePlot2DView
from .view.scatterplot_2d_view import TableScatterPlot2DView
from .view.stacked_barplot_view import TableStackedBarPlotView
from .view.table_view import TableView

ALLOWED_DELIMITER = ["auto", "tab", "space", ",", ";"]
DEFAULT_DELIMITER = "auto"
DEFAULT_FILE_FORMAT = ".csv"


@resource_decorator("Table")
class Table(Resource):

    ALLOWED_DELIMITER = ALLOWED_DELIMITER
    DEFAULT_DELIMITER = DEFAULT_DELIMITER
    DEFAULT_FILE_FORMAT = DEFAULT_FILE_FORMAT

    _data: DataFrame = DataFrameRField()

    def __init__(self, data: Union[DataFrame, np.ndarray, list] = None,
                 column_names=None, row_names=None):
        super().__init__()
        self._set_data(data, column_names, row_names)

    def _set_data(self, data: Union[DataFrame, np.ndarray] = None,
                  column_names=None, row_names=None) -> 'Table':
        if data is None:
            data = DataFrame()
        else:
            if isinstance(data, DataFrame):
                # OK!
                pass
            elif isinstance(data, (np.ndarray, list)):
                data = DataFrame(data)
                if column_names:
                    data.columns = column_names
                if row_names:
                    data.index = row_names
            else:
                raise BadRequestException(
                    "The data must be an instance of DataFrame or Numpy array")

        self._data = data
        return self

    def get_data(self):
        return self._data

    # -- C --

    @property
    def column_names(self) -> list:
        """
        Returns the column names of the Datatable.

        :return: The list of column names or `None` is no column names exist
        :rtype: list or None
        """

        try:
            return self._data.columns.values.tolist()
        except Exception as _:
            return None

    def column_exists(self, name, case_sensitive=True) -> bool:
        if case_sensitive:
            return name in self.column_names
        else:
            lower_names = [x.lower() for x in self.column_names]
            return name.lower() in lower_names

    # -- F --

    @classmethod
    def from_dict(cls, data: dict, orient='index', dtype=None, columns=None) -> 'Table':
        dataframe = DataFrame.from_dict(data, orient, dtype, columns)
        res = cls(data=dataframe)
        return res

    # -- G --

    def get_column(self, column_name: str, rtype='list', skip_nan=False) -> Union['DataFrame', list]:
        if rtype == 'list':
            df = self._data[column_name]
            if skip_nan:
                df.dropna(inplace=True)
            return df.values.tolist()
        else:
            df = self._data[[column_name]]
            if skip_nan:
                df.dropna(inplace=True)
            return df

    # -- H --

    def head(self, n=5) -> DataFrame:
        """
        Returns the first n rows for the columns ant targets.

        :param n: Number of rows
        :param n: int
        :return: The `panda.DataFrame` objects representing the n first rows of the `data`
        :rtype: pandas.DataFrame
        """

        return self._data.head(n)

    # -- I --

    @property
    def is_vector(self) -> bool:
        return self.nb_rows == 1 or self.nb_columns == 1

    @property
    def is_column_vector(self) -> bool:
        return self.nb_columns == 1

    @property
    def is_row_vector(self) -> bool:
        return self.nb_rows == 1

    # -- N --

    @property
    def nb_columns(self) -> int:
        """
        Returns the number of columns.

        :return: The number of columns
        :rtype: int
        """

        return self._data.shape[1]

    @property
    def nb_rows(self) -> int:
        """
        Returns the number of rows.

        :return: The number of rows
        :rtype: int
        """

        return self._data.shape[0]

    # -- R --

    @property
    def row_names(self) -> list:
        """
        Returns the row names.

        :return: The list of row names
        :rtype: list
        """

        return self._data.index.values.tolist()

    def __str__(self):
        return super().__str__() + "\n" + \
            "Table:                                  \n" + \
            self._data.__str__()

    def to_list(self) -> list:
        return self.to_numpy().tolist()

    def to_numpy(self) -> np.ndarray:
        return self._data.to_numpy()

    def to_table(self) -> DataFrame:
        return self._data

    def to_csv(self) -> str:
        return self._data.to_csv()

     # -- T --
    def to_json(self) -> dict:
        return self._data.to_json()

    def tail(self, n=5) -> DataFrame:
        """
        Returns the last n rows for the columns ant targets.

        :param n: Number of rows
        :param n: int
        :return: The `panda.DataFrame` objects representing the n first rows of the `data`
        :rtype: pandas.DataFrame
        """

        return self._data.tail(n)

    def select_by_row_indexes(self, indexes: List[int]) -> 'Table':
        if not isinstance(indexes, list):
            raise BadRequestException("The indexes must be a list of integers")
        data = self._data.iloc[indexes, :]
        return Table(data=data)

    def select_by_column_indexes(self, indexes: List[int]) -> 'Table':
        if not isinstance(indexes, list):
            raise BadRequestException("The indexes must be a list of integers")
        data = self._data.iloc[:, indexes]
        return Table(data=data)

    def select_by_row_name(self, name_regex: str) -> 'Table':
        if not isinstance(name_regex, str):
            raise BadRequestException("The name must be a string")
        data = self._data.filter(regex=name_regex, axis=0)
        return Table(data=data)

    def select_by_column_name(self, name_regex: str) -> 'Table':
        if not isinstance(name_regex, str):
            raise BadRequestException("The name must be a string")
        data = self._data.filter(regex=name_regex, axis=1)
        return Table(data=data)

    # -- V ---

    @view(view_type=TableView, default_view=True, human_name='Tabular', short_description='View as a table', specs={})
    def view_as_table(self, params: ConfigParams) -> TableView:
        """
        View as table
        """

        return TableView(self._data)

    @view(view_type=TableLinePlot2DView, human_name='Line plot 2D', short_description='View columns as 2D-line plots', specs={})
    def view_as_line_plot_2d(self, params: ConfigParams) -> TableLinePlot2DView:
        """
        View columns as 2D-line plots
        """

        return TableLinePlot2DView(self._data)

    # @view(view_type=LinePlot3DView, human_name='LinePlot3D', short_description='View columns as 3D-line plots', specs={})
    # def view_as_line_plot_3d(self, params: ConfigParams) -> LinePlot3DView:
    #     """
    #     View columns as 3D-line plots
    #     """

    #     return LinePlot3DView(self._data)

    # @view(view_type=TableScatterPlot3DView, human_name='ScatterPlot3D', short_description='View columns as 3D-scatter plots', specs={})
    # def view_as_scatter_plot_3d(self, params: ConfigParams) -> TableScatterPlot3DView:
    #     """
    #     View columns as 3D-scatter plots
    #     """

    #     return TableScatterPlot3DView(self._data)

    @view(view_type=TableScatterPlot2DView, human_name='Scatter plot 2D',
          short_description='View columns as 2D-scatter plots', specs={})
    def view_as_scatter_plot_2d(self, params: ConfigParams) -> TableScatterPlot2DView:
        """
        View one or several columns as 2D-line plots
        """

        return TableScatterPlot2DView(self._data)

    @view(view_type=TableBarPlotView, human_name='Bar plot', short_description='View columns as 2D-bar plots', specs={})
    def view_as_bar_plot(self, params: ConfigParams) -> TableBarPlotView:
        """
        View one or several columns as 2D-bar plots
        """

        return TableBarPlotView(self._data)

    @view(view_type=TableStackedBarPlotView, human_name='Stacked bar plot',
          short_description='View columns as 2D-stacked bar plots', specs={})
    def view_as_stacked_bar_plot(self, params: ConfigParams) -> TableStackedBarPlotView:
        """
        View one or several columns as 2D-stacked bar plots
        """

        return TableStackedBarPlotView(self._data)

    @view(view_type=TableHistogramView, human_name='Histogram', short_description='View columns as 2D-line plots', specs={})
    def view_as_histogram(self, params: ConfigParams) -> TableHistogramView:
        """
        View columns as 2D-line plots
        """

        return TableHistogramView(self._data)

    @view(view_type=TableBoxPlotView, human_name='Box plot', short_description='View columns as box plots', specs={})
    def view_as_box_plot(self, params: ConfigParams) -> TableBoxPlotView:
        """
        View one or several columns as box plots
        """

        return TableBoxPlotView(self._data)

    @view(view_type=HeatmapView, human_name='Heatmap', short_description='View table as heatmap', specs={})
    def view_as_heatmap(self, params: ConfigParams) -> HeatmapView:
        """
        View the table as heatmap
        """

        return HeatmapView(self._data)
