# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

import pandas
from pandas import DataFrame

from ....core.exception.exceptions import BadRequestException
from ..metadata_table.metadata_table import MetadataTable
from ..table import Table


class TableTagGrouperHelper:

    ALLOWED_FUNCTIONS = ["mean", "median", "sort"]

    @classmethod
    def group_by_row_tags(cls, table: Table, keys: List[str], func: str = "mean") -> Table:
        """
        Group data along a list of row tag keys

        :param data: A DataFrame comming from and AnnotatedTable (or with annotated key,value columns)
        :param data: DataFrame
        :param data: The tag keys
        :param data: str
        :param data: The grouping function. Allowed values are `mean` and `median`.
        :param data: str
        :param data: The current task that called this help
        :param data: Task
        :return: The DataFrame after row grouping according the `key`
        :rtype: DataFrame
        """

        if func not in cls.ALLOWED_FUNCTIONS:
            raise BadRequestException(f"The grouping function must in {cls.ALLOWED_FUNCTIONS}")

        row_tags = table.get_row_tags()

        if func == "sort":
            tag_dataframe = DataFrame(row_tags, index=table.get_data().index)
            tag_keys = tag_dataframe.columns

            df = pandas.concat([tag_dataframe, table.get_data()], axis=1)
            df.sort_values(by=keys, inplace=True)
            df = df.drop(tag_keys, axis=1)
        else:
            all_tag_keys = list(set([k for t in row_tags for k, v in t.items()]))
            if len(keys) > 1:
                raise BadRequestException("Only one tag key is allowed with `mean` and `median` function")
            key = keys[0]
            if key not in all_tag_keys:
                raise BadRequestException(f"The tag key '{key}' does not exist")

            all_tag_values = list(set([v for t in row_tags for k, v in t.items() if k == key]))
            all_tag_values = sorted(all_tag_values)
            df_list = {}
            for val in all_tag_values:
                grouped_table = table.select_by_row_tags([{key: val}])
                if func == "mean":
                    grouped_table = grouped_table.get_data().mean(axis=0, skipna=True).to_frame().T
                elif func == "median":
                    grouped_table = grouped_table.get_data().median(axis=0, skipna=True).to_frame().T
                df_list[val] = grouped_table
            df = pandas.concat(list(df_list.values()), axis=0)
            df.index = list(df_list.keys())

        return Table(df)

    @classmethod
    def group_by_column_tags(cls, table: Table, keys: List[str], func: str = "mean") -> Table:
        """
        Group data along a list of column tag keys

        :param data: A DataFrame comming from and AnnotatedTable (or with annotated key,value columns)
        :param data: DataFrame
        :param data: The tag keys
        :param data: str
        :param data: The grouping function. Allowed values are `mean` and `median`.
        :param data: str
        :param data: The current task that called this help
        :param data: Task
        :return: The DataFrame after row grouping according the `key`
        :rtype: DataFrame
        """

        if func not in cls.ALLOWED_FUNCTIONS:
            raise BadRequestException(f"The grouping function must in {cls.ALLOWED_FUNCTIONS}")

        column_tags = table.get_column_tags()

        if func == "sort":
            tag_dataframe = DataFrame(column_tags, index=table.get_data().index)
            tag_keys = tag_dataframe.columns

            df = pandas.concat([tag_dataframe, table.get_data()], axis=0)
            df.sort_values(by=keys, inplace=True)
            df = df.drop(tag_keys, axis=0)
        else:
            all_tag_keys = list(set([k for t in column_tags for k, v in t.items()]))
            if len(keys) > 1:
                raise BadRequestException("Only one tag key is allowed with `mean` and `median` function")
            key = keys[0]
            if key not in all_tag_keys:
                raise BadRequestException(f"The tag key '{key}' does not exist")

            all_tag_values = list(set([v for t in column_tags for k, v in t.items() if k == key]))
            all_tag_values = sorted(all_tag_values)
            df_list = {}
            for val in all_tag_values:
                grouped_table = table.select_by_column_tags([{key: val}])
                if func == "mean":
                    grouped_table = grouped_table.get_data().mean(axis=1, skipna=True).to_frame()
                elif func == "median":
                    grouped_table = grouped_table.get_data().median(axis=1, skipna=True).to_frame()
                df_list[val] = grouped_table
            df = pandas.concat(list(df_list.values()), axis=1)
            df.columns = list(df_list.keys())

        return Table(df)
