# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List, Literal

from gws_core.tag.tag_helper import TagHelper
from numpy import nan
from pandas import DataFrame, concat

from ....core.exception.exceptions import BadRequestException
from ....core.utils.utils import Utils
from ..table import AxisType, Table, is_row_axis

TableGroupFunction = Literal['mean', 'median', 'sort']


class TableTagGrouperHelper:

    @classmethod
    def group_by_row_tags(cls, table: Table, keys: List[str], func: TableGroupFunction = "mean") -> Table:
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
        if not Utils.value_is_in_literal(func, TableGroupFunction):
            raise BadRequestException(f"The grouping function must in {Utils.get_literal_values(TableGroupFunction)}")

        if func == "sort":
            return cls.sort_by_row_tags(table, keys)
        else:
            return cls._group_with_aggregate(table.select_numeric_columns(), keys, func, "index")

    @classmethod
    def sort_by_row_tags(cls, table: Table, keys: List[str]) -> Table:
        row_tags = table.get_row_tags()

        tag_dataframe = DataFrame(row_tags, index=table.get_data().index)
        tag_keys = tag_dataframe.columns
        row_positions = DataFrame(
            range(0, tag_dataframe.shape[0]),
            index=table.get_data().index,
            columns=["row_positions"]
        )

        df = concat([row_positions, tag_dataframe, table.get_data()],
                    axis=1)  # add ne columns for multi-row sort

        df.sort_values(by=keys, inplace=True)
        new_row_position = df["row_positions"]
        df = df.drop([*tag_keys.values.tolist(), "row_positions"], axis=1)

        sorted_table = Table(df)
        new_row_tags = [row_tags[i] for i in new_row_position]
        sorted_table.set_row_tags(new_row_tags)
        sorted_table.set_column_tags(table.get_column_tags())
        return sorted_table

    @classmethod
    def unfold_rows_by_tags(cls, table: Table, keys: List[str]) -> Table:
        """Create new column for each column and tags combinaison

        """
        tags: Dict[str, List[str]] = table.get_available_row_tags()

        # filter the tags with the provided keys
        selected_tags: Dict[str, List[str]] = {}
        for key in keys:
            if key in tags:
                selected_tags[key] = tags[key]

        all_tag_combinations = TagHelper.get_all_tags_combinasons(selected_tags)

        dataframe = DataFrame()
        column_tags = []

        for tags in all_tag_combinations:
            sub_table = table.select_by_row_tags([tags])
            df = sub_table.get_data()

            if df.empty:
                continue

            tag_values = '_'.join(tags.values())

            # if the new dataframe has more rows that the previous one
            # we create empty rows to fill the gap
            index_dif = len(df.index) - len(dataframe.index)
            if index_dif > 0 and len(dataframe.index) > 0:
                nan_df = DataFrame([[nan] * len(dataframe.columns)] * index_dif, columns=dataframe.columns)
                dataframe = concat([dataframe, nan_df], ignore_index=True, sort=True)

            for column in df:
                name = f"{column}_{tag_values}"

                # if the new column have fewer rows than dataframe index, append NaN
                values: List[Any] = df[column].values.tolist()
                row_diff = len(dataframe.index) - len(values)
                if row_diff > 0:
                    values.extend([nan] * row_diff)

                dataframe[name] = values

            column_tags.extend(sub_table.get_column_tags())

        table = Table(dataframe)
        table.set_column_tags(column_tags)
        return table

    ############################################## COLUMNS ######################################################

    @classmethod
    def group_by_column_tags(cls, table: Table, keys: List[str], func: TableGroupFunction = "mean") -> Table:
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
        if not Utils.value_is_in_literal(func, TableGroupFunction):
            raise BadRequestException(f"The grouping function must in {Utils.get_literal_values(TableGroupFunction)}")

        if func == "sort":
            return cls.sort_by_column_tags(table, keys)
        else:
            return cls._group_with_aggregate(table.select_numeric_columns(), keys, func, "columns")

    @classmethod
    def sort_by_column_tags(cls, table: Table, keys: List[str]) -> Table:
        column_tags = table.get_column_tags()

        tag_dataframe = DataFrame(column_tags, index=table.get_data().columns)
        tag_keys = tag_dataframe.columns

        column_positions = DataFrame(
            range(0, tag_dataframe.shape[1]),
            columns=table.get_data().columns,
            index=["column_positions"]
        )

        df = concat([column_positions, tag_dataframe, table.get_data()],
                    axis=0)  # add new rows for multi-column sort

        df.sort_values(by=keys, inplace=True, axis=1)
        new_column_position = df["column_positions"]
        df = df.drop([*tag_keys.values.tolist(), "column_positions"], axis=1)

        sorted_table = Table(df)
        new_column_tags = [column_tags[i] for i in new_column_position]
        sorted_table.set_column_tags(new_column_tags)
        sorted_table.set_row_tags(table.get_row_tags())
        return sorted_table

    @classmethod
    def unfold_columns_by_tags(cls, table: Table, keys: List[str]) -> Table:

        tags: Dict[str, List[str]] = table.get_available_column_tags()

        # filter the tags with the provided keys
        selected_tags: Dict[str, List[str]] = {}
        for key in keys:
            if key in tags:
                selected_tags[key] = tags[key]

        all_tag_combinations = TagHelper.get_all_tags_combinasons(selected_tags)

        dataframe = DataFrame()
        row_tags = []

        for tags in all_tag_combinations:
            sub_table = table.select_by_column_tags([tags])
            df = sub_table.get_data()

            if df.empty:
                continue

            tag_values = '_'.join(tags.values())

            for index, row in df.iterrows():
                name = f"{row.name}_{tag_values}"

                # if the new row have fewer column than dataframe, append NaN
                values: List[Any] = row.values.tolist()
                column_diff = len(dataframe.columns) - len(values)
                if column_diff > 0:
                    values.extend([nan] * column_diff)

                row_df = DataFrame([values], index=[name])

                dataframe = concat([dataframe, row_df], sort=True)

            row_tags.extend(sub_table.get_row_tags())

        table = Table(dataframe)
        table.set_row_tags(row_tags)
        return table

    ############################################## BOTH ######################################################

    @classmethod
    def _group_with_aggregate(cls, table: Table, keys: List[str],
                              func: Literal['mean', 'median'], axis: AxisType) -> Table:
        if len(keys) > 1:
            raise BadRequestException("Only one tag key is allowed with `mean` and `median` function")

        tags = table.get_tags(axis)

        all_tag_keys = list(set([k for t in tags for k, v in t.items()]))
        key = keys[0]
        if key not in all_tag_keys:
            raise BadRequestException(f"The tag key '{key}' does not exist")

        all_tag_values = list(set([v for t in tags for k, v in t.items() if k == key]))
        all_tag_values = sorted(all_tag_values)
        df_list = {}
        for val in all_tag_values:
            grouped_table = table.select_by_tags(axis, [{key: val}])
            if func == "mean":
                grouped_table = grouped_table.get_data().mean(axis=axis, skipna=True).to_frame()
            elif func == "median":
                grouped_table = grouped_table.get_data().median(axis=axis, skipna=True).to_frame()
            df_list[val] = grouped_table.T if is_row_axis(axis) else grouped_table

        df: DataFrame = concat(list(df_list.values()), axis=axis)

        if is_row_axis(axis):
            df.index = list(df_list.keys())
            grouped_table = Table(df)
            # set the other axis tags
            grouped_table.set_column_tags(table.get_column_tags())
        else:
            df.columns = list(df_list.keys())
            grouped_table = Table(df)
            # set the other axis tags
            grouped_table.set_row_tags(table.get_row_tags())
        return grouped_table
