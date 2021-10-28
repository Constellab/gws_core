# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from pathlib import Path
from typing import Union

import numpy as np
import pandas
from pandas import DataFrame

from ...config.config_types import ConfigParams
from ...config.param_spec import BoolParam, IntParam, StrParam
from ...core.exception.exceptions import BadRequestException
from ...impl.file.file import File
from ...resource.resource import Resource
from ...resource.resource_decorator import resource_decorator
from ...resource.view_decorator import view
from ...task.exporter import export_to_path
from ...task.importer import import_from_path
from .data_frame_r_field import DataFrameRField
from .view.barplot_view import BarPlotView
from .view.boxplot_view import BoxPlotView
from .view.heatmap_view import HeatmapView
from .view.histogram_view import HistogramView
from .view.lineplot_2d_view import LinePlot2DView
from .view.lineplot_3d_view import LinePlot3DView
from .view.scatterplot_2d_view import ScatterPlot2DView
from .view.scatterplot_3d_view import ScatterPlot3DView
from .view.table_view import TableView


@resource_decorator("Table")
class Table(Resource):

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

    @export_to_path(specs={
        'file_name': StrParam(default_value='file.csv', short_description="Destination file name in the store"),
        'file_format': StrParam(default_value=".csv", short_description="File format"),
        'delimiter': StrParam(default_value="\t", short_description="Delimiter character. Only for parsing CSV files"),
        'header': IntParam(default_value=0, short_description="Write column names (header)"),
        'index': BoolParam(default_value=True, short_description="Write row names (index)"),
        'file_store_uri': StrParam(optional=True, short_description="URI of the file_store where the file must be exported"),
    })
    def export_to_path(self, dir_: str, config: ConfigParams) -> File:
        """
        Export to a repository

        :param file_path: The destination file path
        :type file_path: File
        """
        file_path = os.path.join(dir_, config.get_value('file_name'))

        file_format: str = config.get_value('file_format')
        file_extension = Path(file_path).suffix
        if file_extension in [".xls", ".xlsx"] or file_format in [".xls", ".xlsx"]:
            self._data.to_excel(file_path)
        elif file_extension in [".csv", ".tsv", ".txt", ".tab"] or file_format in [".csv", ".tsv", ".txt", ".tab"]:
            self._data.to_csv(
                file_path,
                sep=config.get_value('delimiter'),
                index=config.get_value('index')
            )
        else:
            raise BadRequestException(
                "Cannot detect the file type using file extension. Valid file extensions are [.xls, .xlsx, .csv, .tsv, .txt, .tab].")

        return File(file_path)

    # -- F --

    @classmethod
    def from_dict(cls, data: dict, orient='index', dtype=None, columns=None) -> 'Table':
        dataframe = DataFrame.from_dict(data, orient, dtype, columns)
        res = cls(data=dataframe)
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

    @property
    def is_vector(self) -> bool:
        return self.nb_rows == 1 or self.nb_columns == 1

    @property
    def is_column_vector(self) -> bool:
        return self.nb_columns == 1

    @property
    def is_row_vector(self) -> bool:
        return self.nb_rows == 1

    @classmethod
    @import_from_path(specs={
        'file_format': StrParam(default_value=".csv", short_description="File format"),
        'delimiter': StrParam(default_value='\t', short_description="Delimiter character. Only for parsing CSV files"),
        'header': IntParam(default_value=0, short_description="Row number to use as the column names. Use None to prevent parsing column names. Only for parsing CSV files"),
        'index': IntParam(optional=True, short_description="Column number to use as the row names. Use None to prevent parsing row names. Only for parsing CSV files"),
    })
    def import_from_path(cls, file: File, config: ConfigParams) -> 'Table':
        """
        Import from a repository

        :param file_path: The source file path
        :type file_path: File
        :returns: the parsed data
        :rtype any
        """

        file_format: str = config.get_value('file_format')
        if file.extension in [".xls", ".xlsx"] or file_format in [".xls", ".xlsx"]:
            df = pandas.read_excel(file.path)
        elif file.extension in [".csv", ".tsv", ".txt", ".tab"] or file_format in [".csv", ".tsv", ".txt", ".tab"]:
            df = pandas.read_table(
                file.path,
                sep=config.get_value('delimiter'),
                header=config.get_value('header'),
                index_col=config.get_value('index')
            )
        else:
            raise BadRequestException(
                "Cannot detect the file type using file extension. Valid file extensions are [.xls, .xlsx, .csv, .tsv, .txt, .tab].")

        return cls(data=df)

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

    # -- V ---

    @view(view_type=TableView, default_view=True, human_name='Tabular', short_description='View as a table', specs={})
    def view_as_table(self, config: ConfigParams) -> TableView:
        """
        View as table
        """

        return TableView(self._data)

    @view(view_type=LinePlot2DView, human_name='LinePlot2D', short_description='View columns as 2D-line plots', specs={})
    def view_as_line_plot_2d(self, config: ConfigParams) -> LinePlot2DView:
        """
        View columns as 2D-line plots
        """

        return LinePlot2DView(self._data)

    @view(view_type=LinePlot3DView, human_name='LinePlot3D', short_description='View columns as 3D-line plots', specs={})
    def view_as_line_plot_3d(self, config: ConfigParams) -> LinePlot3DView:
        """
        View columns as 3D-line plots
        """

        return LinePlot3DView(self._data)

    @view(view_type=ScatterPlot3DView, human_name='ScatterPlot3D', short_description='View columns as 3D-scatter plots', specs={})
    def view_as_scatter_plot_3d(self, config: ConfigParams) -> ScatterPlot3DView:
        """
        View columns as 3D-scatter plots
        """

        return ScatterPlot3DView(self._data)

    @view(view_type=ScatterPlot2DView, human_name='ScatterPlot2D', short_description='View columns as 2D-scatter plots', specs={})
    def view_as_scatter_plot_2d(self, config: ConfigParams) -> ScatterPlot2DView:
        """
        View one or several columns as 2D-line plots
        """

        return ScatterPlot2DView(self._data)

    @view(view_type=BarPlotView, human_name='BarPlot', short_description='View columns as 2D-bar plots', specs={})
    def view_as_bar_plot(self, config: ConfigParams) -> BarPlotView:
        """
        View one or several columns as 2D-bar plots
        """

        return BarPlotView(self._data)

    @view(view_type=HistogramView, human_name='Histogram', short_description='View columns as 2D-line plots', specs={})
    def view_as_histogram(self, config: ConfigParams) -> HistogramView:
        """
        View columns as 2D-line plots
        """

        return HistogramView(self._data)

    @view(view_type=BoxPlotView, human_name='BoxPlot', short_description='View columns as box plots', specs={})
    def view_as_box_plot(self, config: ConfigParams) -> BoxPlotView:
        """
        View one or several columns as box plots
        """

        return BoxPlotView(self._data)

    @view(view_type=HeatmapView, human_name='Heatmap', short_description='View table as heatmap', specs={})
    def view_as_heatmap(self, config: ConfigParams) -> BarPlotView:
        """
        View the table as heatmap
        """

        return HeatmapView(self._data)
