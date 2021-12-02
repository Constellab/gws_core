# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import re

import pandas
from gws_core import MetadataTable
from pandas import DataFrame, Series

from ....core.exception.exceptions import BadRequestException


class TableGroupingHelper:

    @classmethod
    def group_data(cls, data: DataFrame(), key: str, current_task=None):
        """
        Group data according to {key, value} column annotations

        :param data: A DataFrame comming from and AnnotatedTable (or with annotated key,value columns)
        :param data: DataFrame
        :param data: The key use to create groups
        :param data: str
        :param data: The current task that called this help
        :param data: Task
        :return: The DataFrame after column grouping according the the `key`
        :rtype: DataFrame
        """

        pattern = re.compile(f".*{key}{MetadataTable.KEY_VALUE_SEPARATOR}([^{MetadataTable.TOKEN_SEPARATOR}]+).*")
        values = []
        for name in data.columns:
            match = re.match(pattern, str(name))
            if match:
                values.append(match[1])
            else:
                # the filter is not applies
                if current_task:
                    current_task.log_warning_message(
                        f"The grouping filter was aborted. An error occured while search values of key '{key}'.")

        values = sorted(list(set(values)))

        if not values:
            raise BadRequestException(
                f"The grouping filter was aborted. An error occured while search values of key '{key}'.")

        group_data = DataFrame()
        for val in values:
            grouped_col = Series()
            token = MetadataTable.format_token(key, val)
            current_data = data.filter(regex=token)
            for colname in current_data.columns:
                col = current_data.loc[:, colname]
                grouped_col = pandas.concat([grouped_col, col], ignore_index=True)

            group_data = pandas.concat([group_data, grouped_col], axis=1, ignore_index=True)

        group_data.columns = [MetadataTable.format_token(key, val) for val in values]
        # group_data.index = grouped_idx
        return group_data
