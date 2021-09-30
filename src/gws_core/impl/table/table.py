# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from pathlib import Path
from typing import List, Union

import numpy as np
import pandas
from pandas import DataFrame

from ...config.param_spec import IntParam, ListParam, StrParam
from ...core.exception.exceptions import BadRequestException
from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator
from ...resource.view_decorator import view
from .data_frame_r_field import DataFrameRField
from .line_2d_plot_view import Line2DPlotView
from .line_3d_plot_view import Line3DPlotView
from .table_view import TableView


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

    @view(human_name='Line2DView', short_description='View one or several columns as 2D-line plots',
          specs={
              "x_column_name": StrParam(human_name="X-column name", description="The column to use as x-axis"),
              "y_column_names": ListParam(human_name="Y-column names", description="List of columns to use as y-axis"),
              "title": StrParam(default_value="", human_name="Title", description="The plot title"),
              "subtitle": StrParam(default_value="", human_name="Subtitle", description="The plot subtitle")
          })
    def view_as_2d_line_plot(self, *args, **kwargs) -> dict:
        """
        View one or several columns as 2D-line plots
        """

        vw = Line2DPlotView(self._data)
        return vw.to_dict(*args, **kwargs)

    @view(human_name='Line3DView', short_description='View one or several columns as 3D-line plots',
          specs={
              "x_column_name": StrParam(human_name="X-column name", description="The column to use as x-axis"),
              "y_column_name": StrParam(human_name="Y-column name", description="The column to use as y-axis"),
              "z_column_names": ListParam(human_name="Z-column names", description="List of columns to use as z-axis"),
              "title": StrParam(default_value="", human_name="Title", description="The plot title"),
              "subtitle": StrParam(default_value="", human_name="Subtitle", description="The plot subtitle")
          })
    def view_as_3d_line_plot(self, *args, **kwargs) -> dict:
        """
        View one or several columns as 3D-line plots
        """

        vw = Line3DPlotView(self._data)
        return vw.to_dict(*args, **kwargs)

    @view(human_name='TableView', short_description='View as table',
          specs={
              "number_of_rows_per_page": IntParam(default_value=50, min_value=5, max_value=50, human_name="Nb. rows per page"),
              "column_page": IntParam(default_value=1, min_value=1, human_name="Column page"),
              "number_of_columns_per_page": IntParam(default_value=50, min_value=5, max_value=50, human_name="Nb. columns per page"),
              "title": StrParam(default_value="", human_name="Title", description="The table title"),
              "subtitle": StrParam(default_value="", human_name="Subtitle", description="The table subtitle")
          })
    def view_as_table(self, *args, **kwargs) -> dict:
        """
        View as table
        """

        vw = TableView(self._data)
        return vw.to_dict(*args, **kwargs)
