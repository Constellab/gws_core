# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Union

import numpy as np
import pandas
from pandas import DataFrame
from pandas.api.types import is_string_dtype

from ...config.config_types import ConfigParams, ConfigSpecs
from ...core.exception.exceptions import BadRequestException
from ...resource.resource_decorator import resource_decorator
from ...resource.view_decorator import view
from ..table.data_frame_r_field import DataFrameRField
from ..table.table import Table
from ..table.view.barplot_view import TableBarPlotView
from ..table.view.boxplot_view import TableBoxPlotView
from ..table.view.heatmap_view import HeatmapView
from ..table.view.histogram_view import TableHistogramView
from ..table.view.lineplot_2d_view import TableLinePlot2DView
from ..table.view.lineplot_3d_view import TableLinePlot3DView
from ..table.view.scatterplot_2d_view import TableScatterPlot2DView
from ..table.view.scatterplot_3d_view import TableScatterPlot3DView
from ..table.view.stacked_barplot_view import TableStackedBarPlotView
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

    @view(view_type=TableLinePlot2DView, human_name='LinePlot2D', short_description='View columns as 2D-line plots', specs={})
    def view_as_line_plot_2d(self, params: ConfigParams) -> TableLinePlot2DView:
        """
        View columns as 2D-line plots
        """

        return TableLinePlot2DView(self.get_full_data())

    @view(view_type=TableLinePlot3DView, human_name='LinePlot3D', short_description='View columns as 3D-line plots', specs={})
    def view_as_line_plot_3d(self, params: ConfigParams) -> TableLinePlot3DView:
        """
        View columns as 3D-line plots
        """

        return TableLinePlot3DView(self.get_full_data())

    @view(view_type=TableScatterPlot3DView, human_name='ScatterPlot3D',
          short_description='View columns as 3D-scatter plots', specs={})
    def view_as_scatter_plot_3d(self, params: ConfigParams) -> TableScatterPlot3DView:
        """
        View columns as 3D-scatter plots
        """

        return TableScatterPlot3DView(self.get_full_data())

    @view(view_type=TableScatterPlot2DView, human_name='ScatterPlot2D',
          short_description='View columns as 2D-scatter plots', specs={})
    def view_as_scatter_plot_2d(self, params: ConfigParams) -> TableScatterPlot2DView:
        """
        View one or several columns as 2D-line plots
        """

        return TableScatterPlot2DView(self.get_full_data())

    @view(view_type=TableBarPlotView, human_name='BarPlot', short_description='View columns as 2D-bar plots', specs={})
    def view_as_bar_plot(self, params: ConfigParams) -> TableBarPlotView:
        """
        View one or several columns as 2D-bar plots
        """

        return TableBarPlotView(self.get_full_data())

    @view(view_type=TableStackedBarPlotView, human_name='StackedBarPlot',
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

        return TableHistogramView(self.get_full_data())

    @view(view_type=TableBoxPlotView, human_name='BoxPlot', short_description='View columns as box plots', specs={})
    def view_as_box_plot(self, params: ConfigParams) -> TableBoxPlotView:
        """
        View one or several columns as box plots
        """

        return TableBoxPlotView(self.get_full_data())

    @view(view_type=HeatmapView, human_name='Heatmap', short_description='View table as heatmap', specs={})
    def view_as_heatmap(self, params: ConfigParams) -> TableBarPlotView:
        """
        View the table as heatmap
        """

        return HeatmapView(self.get_full_data())
