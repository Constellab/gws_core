# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from pathlib import Path
from typing import List, Union

import numpy as np
import pandas
from pandas import DataFrame
from pandas.api.types import is_string_dtype

from ...config.config_types import ConfigParams
from ...config.param_spec import BoolParam, IntParam, ListParam, StrParam
from ...core.exception.exceptions import BadRequestException
from ...impl.file.file import File
from ...resource.resource_decorator import resource_decorator
from ...resource.view_decorator import view
from ...task.exporter import export_to_path, exporter_decorator
from ...task.importer import import_from_path, importer_decorator
from ..table.data_frame_r_field import DataFrameRField
from ..table.table import Table
from ..table.table_tasks import TableExporter, TableImporter
from ..table.view.barplot_view import BarPlotView
from ..table.view.boxplot_view import BoxPlotView
from ..table.view.heatmap_view import HeatmapView
from ..table.view.histogram_view import HistogramView
from ..table.view.lineplot_2d_view import LinePlot2DView
from ..table.view.lineplot_3d_view import LinePlot3DView
from ..table.view.scatterplot_2d_view import ScatterPlot2DView
from ..table.view.scatterplot_3d_view import ScatterPlot3DView
from ..table.view.stacked_barplot_view import StackedBarPlotView
from .view.dataset_view import DatasetView

# ====================================================================================================================
# ====================================================================================================================


@resource_decorator("Dataset")
class Dataset(Table):
    """
    Dataset class
    """

    _data: DataFrame = DataFrameRField()    # features
    _targets: DataFrame = DataFrameRField()

    def __init__(self, features: Union[DataFrame, np.ndarray] = None,
                 targets: Union[DataFrame, np.ndarray] = None,
                 feature_names: List[str] = None, target_names: List[str] = None, row_names: List[str] = None):
        super().__init__()
        self._set_features_and_targets(features=features, targets=targets,
                                       feature_names=feature_names, target_names=target_names, row_names=row_names)

    # -- C --

    @property
    def column_names(self) -> list:
        """
        Returns the feature and tagert names
        """

        return [*self.feature_names, *self.target_names]

    # -- E --
    @export_to_path(specs={
        'file_name': StrParam(default_value="file.csv", short_description="File name"),
        'file_format': StrParam(default_value=".csv", short_description="File format"),
        'delimiter': StrParam(default_value="\t", short_description="Delimiter character. Only for parsing CSV files"),
        'write_header': BoolParam(optional=True, short_description="True to write column names (header), False otherwise"),
        'write_index': BoolParam(optional=True, short_description="True to write row names (index), Fasle otherwise"),
    })
    def export_to_path(self, dest_dir, params: ConfigParams):
        """
        Export to a repository

        :param file_path: The destination file path
        :type file_path: File
        """

        file_name = params.get_value("file_name", "file.csv")

        file_path = os.path.join(dest_dir, file_name)
        file_extension = Path(file_path).suffix or params.get_value("file_format", ".csv")
        if file_extension in [".xls", ".xlsx"] or file_extension in [".xls", ".xlsx"]:
            table = self.get_full_data()
            table.to_excel(file_path)
        elif file_extension in [".csv", ".tsv", ".txt", ".tab"] or file_extension in [".csv", ".tsv", ".txt", ".tab"]:
            table = self.get_full_data()
            table.to_csv(
                file_path,
                sep=params.get_value("delimiter", "\t"),
                header=params.get_value("write_header", True),
                index=params.get_value("write_index", True)
            )
        else:
            raise BadRequestException(
                "Cannot detect the file type using file extension. Valid file extensions are [.xls, .xlsx, .csv, .tsv, .txt, .tab].")

    # -- F --

    def get_full_data(self) -> DataFrame:
        return pandas.concat([self._data, self._targets])

    def get_features(self) -> DataFrame:
        return self._data

    def get_targets(self) -> DataFrame:
        return self._targets

    @property
    def feature_names(self) -> list:
        """
        Returns the feaures names of the Dataset.

        :return: The list of feature names or `None` is no feature names exist
        :rtype: list or None
        """
        try:
            return self._data.columns.values.tolist()
        except:
            return None

    def feature_exists(self, name) -> bool:
        return name in self.feature_names

    # -- H --

    def head(self, n=5) -> (DataFrame, DataFrame):
        """
        Returns the first n rows for the features ant targets.

        :param n: Number of rows
        :param n: int
        :return: Two `panda.DataFrame` objects representing the n first rows of the `features` and `targets`
        :rtype: tuple, (pandas.DataFrame, pandas.DataFrame)
        """

        features = self._data.head(n)
        if self._targets is None:
            targets = None
        else:
            targets = self._targets.head(n)

        return features, targets

    # -- I --

    @classmethod
    @import_from_path(specs={
        'file_format': StrParam(default_value=".csv", short_description="File format"),
        'delimiter': StrParam(default_value='\t', short_description="Delimiter character. Only for parsing CSV files"),
        'header': IntParam(optional=True, default_value=0, short_description="Row number to use as the column names. Use -1 to prevent parsing column names. Only for parsing CSV files"),
        'index_columns': ListParam(optional=True, short_description="Columns to use as the row names. Use None to prevent parsing row names. Only for parsing CSV files"),
        'targets': ListParam(default_value='[]', short_description="List of integers or strings (eg. ['name', 6, '7'])"),
    })
    def import_from_path(cls, file: File, params: ConfigParams) -> 'Dataset':
        """
        Import from a repository

        :param file_path: The source file path
        :type file_path: file path
        :returns: the parsed data
        :rtype any
        """

        delimiter = params.get_value("delimiter", '\t')
        header = params.get_value("header", 0)
        index_col = params.get_value("index_columns")
        #file_format = params.get_value("file_format")
        targets = params.get_value("targets", [])
        _, file_extension = os.path.splitext(file.path)

        if file_extension in [".xls", ".xlsx"]:
            df = pandas.read_excel(file.path)
        elif file_extension in [".csv", ".tsv", ".txt", ".tab"]:
            df = pandas.read_table(
                file.path,
                sep=delimiter,
                header=(None if header < 0 else header),
                index_col=index_col
            )
        else:
            raise BadRequestException(
                "Cannot detect the file type using file extension. Valid file extensions are [.xls, .xlsx, .csv, .tsv, .txt, .tab].")

        if not targets:
            ds = cls(features=df)
        else:
            try:
                t_df = df.loc[:, targets]
            except Exception as err:
                raise BadRequestException(
                    f"The targets {targets} are no found in column names. Please check targets names or set parameter 'header' to read column names.") from err
            df.drop(columns=targets, inplace=True)
            ds = cls(features=df, targets=t_df)
        return ds

    @property
    def instance_names(self) -> list:
        """
        Returns the instance names.

        :return: The list of instance names
        :rtype: list
        """
        return self._data.index.values.tolist()

    # -- N --

    @property
    def nb_features(self) -> int:
        """
        Returns the number of features.

        :return: The number of features
        :rtype: int
        """
        return self._data.shape[1]

    @property
    def nb_instances(self) -> int:
        """
        Returns the number of instances.

        :return: The number of instances
        :rtype: int
        """
        return self._data.shape[0]

    @property
    def nb_targets(self) -> int:
        """
        Returns the number of targets.

        :return: The number of targets (0 is no targets exist)
        :rtype: int
        """
        if self._targets is None:
            return 0
        else:
            return self._targets.shape[1]

    @property
    def nb_columns(self) -> int:
        """
        Returns the total number of columns (number of features + number of targets)

        :return: The total number of columns
        :rtype: int
        """

        return self.nb_features + self.nb_targets

    @property
    def nb_rows(self) -> int:
        """
        Returns the total number of rows

        :return: The total number of columns
        :rtype: int
        """

        return max(self._data.shape[0], self._targets.shape[0])

    # -- R --

    @property
    def row_names(self) -> list:
        """
        Alias of :property:`instance_names`
        """

        return self.instance_names

    # -- S --

    def __str__(self):
        return super().__str__() + "\n" + \
            "Features:\n" + \
            self._data.__str__() + "\n\n" + \
            "Targets:\n" + \
            self._targets.__str__()

    def set_data(self, *args, **kwargs):
        raise BadRequestException("Not implemented for Dataset")

    def set_features(self, data: DataFrame):
        self._data = data

    def set_targets(self, targets: DataFrame):
        self._targets = targets

    def select_by_row_indexes(self, indexes: List[int], only_features=False, only_targets=False) -> 'Dataset':
        if not isinstance(indexes, list):
            raise BadRequestException("The indexes must be a list of integers")
        data = DataFrame()
        targets = DataFrame()
        if not only_targets:
            data = self._data.iloc[indexes, :]
        if not only_features:
            targets = self._targets.iloc[indexes, :]
        return Dataset(features=data, targets=targets)

    def select_by_column_indexes(self, indexes: List[int], only_features=False, only_targets=False) -> 'Dataset':
        if not isinstance(indexes, list):
            raise BadRequestException("The indexes must be a list of integers")
        data = DataFrame()
        targets = DataFrame()
        n = self.nb_features
        feature_indexes = [i for i in indexes if i < n]
        target_indexes = [i-n for i in indexes if i >= n]

        if not only_targets:
            data = self._data.iloc[:, feature_indexes]
        if not only_features:
            targets = self._targets.iloc[:, target_indexes]
        return Dataset(features=data, targets=targets)

    def select_by_row_name(self, name_regex: str, only_features=False, only_targets=False) -> 'Dataset':
        if not isinstance(name_regex, str):
            raise BadRequestException("The name must be a string")
        data = DataFrame()
        targets = DataFrame()
        if not only_targets:
            data = self._data.filter(regex=name_regex, axis=0)
        if not only_features:
            targets = self._targets.filter(regex=name_regex, axis=0)
        return Dataset(features=data, targets=targets)

    def select_by_column_name(self, name_regex: str, only_features=False, only_targets=False) -> 'Dataset':
        if not isinstance(name_regex, str):
            raise BadRequestException("The name must be a string")
        data = DataFrame()
        targets = DataFrame()
        if not only_targets:
            data = self._data.filter(regex=name_regex, axis=1)
        if not only_features:
            targets = self._targets.filter(regex=name_regex, axis=1)
        return Dataset(features=data, targets=targets)

    def _set_features_and_targets(
            self, features: Union[DataFrame, np.ndarray] = None, targets: Union[DataFrame, np.ndarray] = None,
            feature_names: List[str] = None, target_names: List[str] = None, row_names: List[str] = None):

        if features is not None:
            if isinstance(features, DataFrame):
                # OK!
                pass
            elif isinstance(features, (np.ndarray, list)):
                features = DataFrame(features)
                if feature_names:
                    features.columns = feature_names
                if row_names:
                    features.index = row_names
            else:
                raise BadRequestException(
                    "The table mus be an instance of DataFrame or Numpy array")
            self._data = features

        if targets is not None:
            if isinstance(targets, DataFrame):
                # OK!
                pass
            elif isinstance(targets, (np.ndarray, list)):
                targets = DataFrame(targets)
                if target_names:
                    targets.columns = target_names
                if row_names:
                    targets.index = row_names
            else:
                raise BadRequestException(
                    "The table mus be an instance of DataFrame or Numpy array")
            self._targets = targets

        return self

    # -- T --

    @property
    def target_names(self) -> list:
        """
        Returns the target names.

        :return: The list of target names or `None` is no target names exist
        :rtype: list or None
        """
        try:
            return self._targets.columns.values.tolist()
        except:
            return None

    def target_exists(self, name) -> bool:
        return name in self.target_names

    def has_string_targets(self):
        return is_string_dtype(self._targets)

    def convert_targets_to_dummy_matrix(self) -> DataFrame:
        if self._targets.shape[1] != 1:
            raise BadRequestException("The target vector must be a column vector")
        labels = sorted(list(set(self._targets.transpose().values.tolist()[0])))
        nb_labels = len(labels)
        nb_instances = self._targets.shape[0]
        data = np.zeros(shape=(nb_instances, nb_labels))
        for i in range(0, nb_instances):
            current_label = self._targets.iloc[i, 0]
            idx = labels.index(current_label)
            data[i][idx] = 1.0
        return DataFrame(data=data, index=self._targets.index, columns=labels)

    # -- V ---

    @view(view_type=DatasetView, default_view=True, human_name='Tabular', short_description='View as a table', specs={})
    def view_as_table(self, params: ConfigParams) -> DatasetView:
        """
        View as table
        """

        return DatasetView(self)

    # @view(view_type=TableView, default_view=True, human_name='Raw Tabular', short_description='View as a table', specs={})
    # def view_as_table(self, params: ConfigParams) -> TableView:
    #     """
    #     View as table
    #     """
    #     return TableView(self.get_full_data())

    @view(view_type=LinePlot2DView, human_name='LinePlot2D', short_description='View columns as 2D-line plots', specs={})
    def view_as_line_plot_2d(self, params: ConfigParams) -> LinePlot2DView:
        """
        View columns as 2D-line plots
        """

        return LinePlot2DView(self.get_full_data())

    @view(view_type=LinePlot3DView, human_name='LinePlot3D', short_description='View columns as 3D-line plots', specs={})
    def view_as_line_plot_3d(self, params: ConfigParams) -> LinePlot3DView:
        """
        View columns as 3D-line plots
        """

        return LinePlot3DView(self.get_full_data())

    @view(view_type=ScatterPlot3DView, human_name='ScatterPlot3D', short_description='View columns as 3D-scatter plots', specs={})
    def view_as_scatter_plot_3d(self, params: ConfigParams) -> ScatterPlot3DView:
        """
        View columns as 3D-scatter plots
        """

        return ScatterPlot3DView(self.get_full_data())

    @view(view_type=ScatterPlot2DView, human_name='ScatterPlot2D', short_description='View columns as 2D-scatter plots', specs={})
    def view_as_scatter_plot_2d(self, params: ConfigParams) -> ScatterPlot2DView:
        """
        View one or several columns as 2D-line plots
        """

        return ScatterPlot2DView(self.get_full_data())

    @view(view_type=BarPlotView, human_name='BarPlot', short_description='View columns as 2D-bar plots', specs={})
    def view_as_bar_plot(self, params: ConfigParams) -> BarPlotView:
        """
        View one or several columns as 2D-bar plots
        """

        return BarPlotView(self.get_full_data())

    @view(view_type=StackedBarPlotView, human_name='BarPlot', short_description='View columns as 2D-stacked bar plots', specs={})
    def view_as_stacked_bar_plot(self, params: ConfigParams) -> BarPlotView:
        """
        View one or several columns as 2D-stacked bar plots
        """

        return StackedBarPlotView(self._data)

    @view(view_type=HistogramView, human_name='Histogram', short_description='View columns as 2D-line plots', specs={})
    def view_as_histogram(self, params: ConfigParams) -> HistogramView:
        """
        View columns as 2D-line plots
        """

        return HistogramView(self.get_full_data())

    @view(view_type=BoxPlotView, human_name='BoxPlot', short_description='View columns as box plots', specs={})
    def view_as_box_plot(self, params: ConfigParams) -> BoxPlotView:
        """
        View one or several columns as box plots
        """

        return BoxPlotView(self.get_full_data())

    @view(view_type=HeatmapView, human_name='Heatmap', short_description='View table as heatmap', specs={})
    def view_as_heatmap(self, params: ConfigParams) -> BarPlotView:
        """
        View the table as heatmap
        """

        return HeatmapView(self.get_full_data())


# ====================================================================================================================
# ====================================================================================================================


@importer_decorator(unique_name="DatasetImporter", resource_type=Dataset)
class DatasetImporter(TableImporter):
    pass


@exporter_decorator("DatasetExporter", resource_type=Dataset)
class DatasetExporter(TableExporter):
    pass
