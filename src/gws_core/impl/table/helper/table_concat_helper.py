# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, List, Literal

from pandas import NA, DataFrame, concat, isna

from gws_core.core.utils.utils import Utils
from gws_core.impl.table.helper.dataframe_helper import DataframeHelper
from gws_core.impl.table.table import Table

# Option to handle the opposite tags during concat. Ex column tags during row contat
#     - ignore: the tags are ignored and left empty
#     - keep first: only the tags of the first table are keept
#     - keep second: only the tags of the second table are keept
#     - merge from first: tags of the first and second table are merged (the first table tags override the second table tags)
#     - merge from second: tags of the first and second table are merged (the second table tags override the first table tags)
TableConcatOppositeTagOption = Literal['ignore', 'keep first', 'keep second', 'merge from first', 'merge from second']


class TableConcatHelper:

    OPPOSITE_TAG_OPTIONS = Utils.get_literal_values(TableConcatOppositeTagOption)

    @classmethod
    def concat_table_rows(cls, table_1: Table, table_2: Table,
                          column_tags_option: TableConcatOppositeTagOption = 'ignore',
                          fill_nan: Any = NA) -> Table:
        """Concatenate two tables along the rows.
        The total number of rows will be the sum of the two tables. The total number of columns will depend if the two table
        have common columns (based on name).
        If the two table have the same column (based on name), the values of theses columns are concatenated starting from
        the first table into the same column.

        If a column doesn't exist in the other table, it will be concatenate with value provided in fill_nan.

        :param table_1: first table
        :type table_1: Table
        :param table_2: second table
        :type table_2: Table
        :param column_tags_option: Option for the columns tags, defaults to 'ignore'
        :type column_tags_option: TableConcatOppositeTagOption, optional
        :param fill_empty: value to replace NA with. , defaults to NA
        :type fill_empty: Any, optional
        :return: _description_
        :rtype: Table
        """

        concat_df = concat([table_1.get_data(), table_2.get_data()])

        row_tags = table_1.get_row_tags() + table_2.get_row_tags()

        # retrieve column tags based on opposite_tag_option
        column_tags: List[dict] = None
        if column_tags_option == 'keep first':
            column_tags = cls._get_column_tags(concat_df, table_1)
        elif column_tags_option == 'keep second':
            column_tags = cls._get_column_tags(concat_df, table_2)
        elif column_tags_option == 'merge from first':
            column_tags = cls._get_merge_column_tags(concat_df, table_1, table_2)
        elif column_tags_option == 'merge from second':
            column_tags = cls._get_merge_column_tags(concat_df, table_2, table_1)

        # fill empty values based on fill_empty
        # do nothing for NaN, it is already NaN
        if fill_nan is None:
            concat_df.replace({NA: None}, inplace=True)
        elif isna(fill_nan):
            pass
        else:
            concat_df.fillna(fill_nan, inplace=True)

        # the concatenation might produce duplicate row names in the result, rename them
        # rename after getting the tags
        concat_df = DataframeHelper.rename_duplicate_row_names(concat_df)

        return Table(concat_df, row_tags=row_tags, column_tags=column_tags)

    @classmethod
    def concat_table_columns(cls, table_1: Table, table_2: Table,
                             row_tags_option: TableConcatOppositeTagOption = 'ignore',
                             fill_nan: Any = NA) -> Table:
        """Concatenate two tables along the columns.
        The total number of columns will be the sum of the two tables. The total number of rows will depend if the two table
        have common rows (based on name).
        If the two table have the same row (based on name), the values of theses rows are concatenated starting from
        the first table into the same row.

        If a row doesn't exist in the other table, it will be concatenate with value provided in fill_nan.

        :param table_1: first table
        :type table_1: Table
        :param table_2: second table
        :type table_2: Table
        :param row_tag_option: Option for the rows tags, defaults to 'ignore'
        :type row_tag_option: TableConcatOppositeTagOption, optional
        :param fill_empty: value to replace NaN with. , defaults to NaN
        :type fill_empty: Any, optional
        :return: _description_
        :rtype: Table
        """

        t_table_1 = table_1.transpose()
        t_table_2 = table_2.transpose()

        result = cls.concat_table_rows(t_table_1, t_table_2, row_tags_option, fill_nan)

        return result.transpose(convert_dtypes=True)

    @classmethod
    def _get_column_tags(cls, concat_df: DataFrame, table: Table) -> List[dict]:
        """For each concat_df columns take the tag from the table with same column name"""
        tag_list: List[dict] = []
        for column_name in concat_df:
            if table.column_exists(column_name):
                tag_list.append(table.get_column_tag_by_name(column_name))
            else:
                tag_list.append({})
        return tag_list

    @classmethod
    def _get_merge_column_tags(cls, concat_df: DataFrame, main_table: Table, second_table: Table) -> List[dict]:
        """
        For each concat_df columns merge the tags from the main_table and second_table (with same column name),
        tags from main_table are preferred
        """

        tag_list: List[dict] = []
        for column_name in concat_df:
            tags = {}

            # get the tags from the second table
            if second_table.column_exists(column_name):
                tags = second_table.get_column_tag_by_name(column_name)

            # update the tags with the main table
            if main_table.column_exists(column_name):
                tags.update(main_table.get_column_tag_by_name(column_name))

            tag_list.append(tags)
        return tag_list
