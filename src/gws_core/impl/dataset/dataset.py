# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Union, final

import numpy as np
from gws_core.impl.table.table_types import TableMeta
from pandas import DataFrame
from pandas.api.types import is_string_dtype

from ...config.config_types import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...impl.table.data_frame_r_field import DataFrameRField
from ...impl.table.table import Table
from ...resource.r_field import ListRField
from ...resource.resource_decorator import resource_decorator
from ...resource.view_decorator import view
from .dataset_view import DatasetView


@final
@resource_decorator("Dataset", human_name="Dataset",
                    short_description="Data table for statistical and machine learning analysis")
class Dataset(Table):
    """
    Dataset class
    """

    _data: DataFrame = DataFrameRField()
    _feature_positions: List[int] = ListRField()
    _target_positions: List[int] = ListRField()

    def __init__(self, data: Union[DataFrame, np.ndarray, list] = None,
                 row_names=None, column_names=None, target_names: List[str] = None, meta: List = None):
        super().__init__(data, row_names=row_names, column_names=column_names, meta=meta)
        self._set_target_names(target_names)

    def set_target_names(self, target_names: List = None):
        self._set_target_names(target_names)

    def _set_target_names(self, target_names: List = None):
        if (target_names is not None) and not isinstance(target_names, list):
            raise BadRequestException("The target_names an instance of list")

        if target_names:
            if not isinstance(target_names, list):
                raise BadRequestException("The target names must be a list")

            target_positions = [i for i, name in enumerate(self._data.columns) if name in target_names]
            if len(target_positions) != len(target_names):
                invalid_target_names = [name for name in target_names if name not in self._data.columns]
                raise BadRequestException(
                    f"The following target names {invalid_target_names} were not found in the column names of data")
            self._target_positions = target_positions
            self._feature_positions = [i for i, name in enumerate(self._data.columns) if name not in target_names]
        else:
            self._target_positions = []
            self._feature_positions = list(range(0, self._data.shape[1]))

    # -- C --

    # -- F --

    @classmethod
    def from_table(cls, table: Table) -> 'Dataset':
        """
        Create a Dataset from a Table
        """
        dataset = cls(
            data=table.get_data(),
            meta=table.get_meta()
        )
        return dataset

    def get_features(self) -> DataFrame:
        """
        Get features
        """
        return self._data.iloc[:, self._feature_positions]

    def get_targets(self) -> DataFrame:
        """
        Get targets
        """
        return self._data.iloc[:, self._target_positions]

    @ property
    def feature_names(self) -> list:
        """
        Returns the feaures names of the Dataset.

        :return: The list of feature names or `None` is no feature names exist
        :rtype: list or None
        """

        return self._data.columns[self._feature_positions].values.tolist()

    def feature_exists(self, name) -> bool:
        """
        Check if a feature exists
        """

        return name in self.feature_names

    # -- H --

    def has_string_targets(self):
        """
        Check if some targets contain string data types
        """
        return is_string_dtype(self.get_targets())

    # -- I --

    @ property
    def instance_names(self) -> list:
        """
        Returns the instance names. Alias of `row_names`

        :return: The list of instance names
        :rtype: list
        """
        return self.row_names

    # -- N --

    @ property
    def nb_features(self) -> int:
        """
        Returns the number of features.

        :return: The number of features
        :rtype: int
        """
        return len(self._feature_positions)

    @ property
    def nb_instances(self) -> int:
        """
        Returns the number of instances.

        :return: The number of instances
        :rtype: int
        """
        return self._data.shape[0]

    @ property
    def nb_targets(self) -> int:
        """
        Returns the number of targets.

        :return: The number of targets (0 is no targets exist)
        :rtype: int
        """

        return len(self._target_positions)

    @ property
    def nb_columns(self) -> int:
        """
        Returns the total number of columns (number of features + number of targets)

        :return: The total number of columns
        :rtype: int
        """

        return self._data.shape[1]

    def _create_sub_table(self, dataframe: DataFrame, meta: TableMeta) -> 'Table':
        dataset: Dataset = super()._create_sub_table(dataframe, meta)
        new_target_names = [name for name in self.target_names if name in dataset.column_names]
        dataset._set_target_names(new_target_names)
        return dataset

    # -- T --

    @ property
    def target_names(self) -> list:
        """
        Returns the target names.

        :return: The list of target names or `None` is no target names exist
        :rtype: list or None
        """
        return self._data.columns[self._target_positions].values.tolist()

    def target_exists(self, name) -> bool:
        return name in self.target_names

    def convert_row_tags_to_dummy_target_matrix(self, key: str) -> DataFrame:
        tags = self.get_row_tags()
        targets = [tag[key] for tag in tags]
        labels = sorted(list(set(targets)))
        nb_labels = len(labels)
        nb_instances = len(targets)
        data = np.zeros(shape=(nb_instances, nb_labels))
        for i in range(0, nb_instances):
            current_label = targets[i]
            idx = labels.index(current_label)
            data[i][idx] = 1.0

        return DataFrame(data=data, index=targets, columns=labels)

    def convert_targets_to_dummy_matrix(self) -> DataFrame:
        targets = self.get_targets()
        if targets.shape[1] != 1:
            raise BadRequestException("The target vector must be a column vector")
        labels = sorted(list(set(targets.transpose().values.tolist()[0])))
        nb_labels = len(labels)
        nb_instances = targets.shape[0]
        data = np.zeros(shape=(nb_instances, nb_labels))
        for i in range(0, nb_instances):
            current_label = targets.iloc[i, 0]
            idx = labels.index(current_label)
            data[i][idx] = 1.0
        return DataFrame(data=data, index=targets.index, columns=labels)

    # -- V ---

    @view(view_type=DatasetView, default_view=True, human_name='Tabular', short_description='View as a table', specs={})
    def view_as_table(self, params: ConfigParams) -> DatasetView:
        """
        View as table
        """

        return DatasetView(self)
