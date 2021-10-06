# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pathlib import Path
from typing import List, Union

import numpy as np
import pandas
from pandas import DataFrame

from ...config.param_spec import BoolParam, IntParam, ListParam, StrParam
from ...core.exception.exceptions import BadRequestException
from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator
from ...resource.view_decorator import view
from .data_frame_r_field import DataFrameRField
from .view.histogram_view import HistogramView
from .view.lineplot_2d_view import LinePlot2DView
from .view.lineplot_3d_view import LinePlot3DView
from .view.scatterplot_2d_view import ScatterPlot2DView
from .view.scatterplot_3d_view import ScatterPlot3DView
from .view.table_view import TableView


@resource_decorator("Table")
class Table(Resource):

    _data: DataFrame = DataFrameRField()

    def set_data(self, data: Union[DataFrame, np.ndarray] = None,
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

    def export_to_path(self, file_path: str, delimiter: str = "\t", header: bool = True, index: bool = True,
                       file_format: str = None, **kwargs):
        """
        Export to a repository

        :param file_path: The destination file path
        :type file_path: File
        """

        file_extension = Path(file_path).suffix
        if file_extension in [".xls", ".xlsx"] or file_format in [".xls", ".xlsx"]:
            self._data.to_excel(file_path)
        elif file_extension in [".csv", ".tsv", ".txt", ".tab"] or file_format in [".csv", ".tsv", ".txt", ".tab"]:
            self._data.to_csv(
                file_path,
                sep=delimiter,
                index=index
            )
        else:
            raise BadRequestException(
                "Cannot detect the file type using file extension. Valid file extensions are [.xls, .xlsx, .csv, .tsv, .txt, .tab].")

    # -- F --

    @classmethod
    def from_dict(cls, data: dict, orient='index', dtype=None, columns=None) -> 'Table':
        dataframe = DataFrame.from_dict(data, orient, dtype, columns)
        res = cls()
        res.set_data(dataframe)
        return res

    # -- G --

    def get_column(self, column_name: str, rtype='list') -> Union['DataFrame', list]:
        if rtype == 'list':
            return list(self._data[column_name].values)
        else:
            return self._data[[column_name]]

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

    @classmethod
    def import_from_path(cls, file_path: str, delimiter: str = "\t", header=0, index_col=None, file_format: str = None, **
                         kwargs) -> 'Table':
        """
        Import from a repository

        :param file_path: The source file path
        :type file_path: File
        :returns: the parsed data
        :rtype any
        """

        file_extension = Path(file_path).suffix
        if file_extension in [".xls", ".xlsx"] or file_format in [".xls", ".xlsx"]:
            df = pandas.read_excel(file_path)
        elif file_extension in [".csv", ".tsv", ".txt", ".tab"] or file_format in [".csv", ".tsv", ".txt", ".tab"]:
            df = pandas.read_table(
                file_path,
                sep=delimiter,
                header=header,
                index_col=index_col
            )
        else:
            raise BadRequestException(
                "Cannot detect the file type using file extension. Valid file extensions are [.xls, .xlsx, .csv, .tsv, .txt, .tab].")

        return cls().set_data(data=df)

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
        return self._data.__str__()

    def to_table(self):
        return self._data

    def to_csv(self, **kwargs):
        return self._data.to_csv()

     # -- T --
    def to_json(self, **kwargs) -> dict:
        return self._data.to_json()

    # -- V ---

    @view(view_type=TableView, human_name='Tabular', short_description='View as a table',
          specs={})
    def view_as_table(self) -> TableView:
        """
        View as table
        """

        return TableView(self._data)

    @view(view_type=LinePlot2DView, human_name='LinePlot2D', short_description='View columns as 2D-line plots',
          specs={
              "x_column_name": StrParam(human_name="X-column name", short_description="The column to use as x-axis"),
              "y_column_names": ListParam(human_name="Y-column names", short_description="List of columns to use as y-axis")
          })
    def view_as_line_plot_2d(self, *args, **kwargs) -> LinePlot2DView:
        """
        View columns as 2D-line plots
        """

        return LinePlot2DView(self._data, *args, **kwargs)

    @view(view_type=LinePlot3DView, human_name='LinePlot3D', short_description='View columns as 3D-line plots',
          specs={
              "x_column_name": StrParam(human_name="X-column name", short_description="The column to use as x-axis"),
              "y_column_name": StrParam(human_name="Y-column name", short_description="The column to use as y-axis"),
              "z_column_names": ListParam(human_name="Z-column names", short_description="List of columns to use as z-axis"),
          })
    def view_as_line_plot_3d(self, *args, **kwargs) -> LinePlot3DView:
        """
        View columns as 3D-line plots
        """

        return LinePlot3DView(self._data, *args, **kwargs)

    @view(view_type=ScatterPlot3DView, human_name='ScatterPlot3D', short_description='View columns as 3D-scatter plots',
          specs={
              "x_column_name": StrParam(human_name="X-column name", short_description="The column to use as x-axis"),
              "y_column_names": ListParam(human_name="Y-column names", short_description="List of columns to use as y-axis")
          })
    def view_as_scatter_plot_3d(self, *args, **kwargs) -> ScatterPlot3DView:
        """
        View columns as 3D-scatter plots
        """

        return ScatterPlot3DView(self._data, *args, **kwargs)

    @view(view_type=ScatterPlot2DView, human_name='ScatterPlot2D', short_description='View columns as 2D-scatter plots',
          specs={
              "x_column_name": StrParam(human_name="X-column name", short_description="The column to use as x-axis"),
              "y_column_names": ListParam(human_name="Y-column names", short_description="List of columns to use as y-axis")
          })
    def view_as_scatter_plot_2d(self, *args, **kwargs) -> ScatterPlot2DView:
        """
        View one or several columns as 2D-line plots
        """

        return ScatterPlot2DView(self._data, *args, **kwargs)

    @view(view_type=HistogramView, human_name='Histogram', short_description='View columns as 2D-line plots',
          specs={
              "column_names": ListParam(human_name="Column names", short_description="List of columns to view"),
              "nbins": IntParam(default_value=10, min_value=0, human_name="Nbins", short_description="The number of bins. Set zero (0) for auto."),
              "density": BoolParam(default_value=False, human_name="Density", short_description="True to pplot density")
          })
    def view_as_histogram(self, *args, **kwargs) -> HistogramView:
        """
        View columns as 2D-line plots
        """

        return HistogramView(self._data, *args, **kwargs)
