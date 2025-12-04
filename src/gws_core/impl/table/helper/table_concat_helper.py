from typing import Any, List, Literal

from numpy import NaN
from pandas import DataFrame, concat, isna

from gws_core.core.utils.utils import Utils
from gws_core.impl.table.table import Table

# Option to handle the opposite tags during concat. Ex column tags during row contat
#     - ignore: the tags are ignored and left empty
#     - keep first: only the tags of the first table are keept
#     - keep second: only the tags of the second table are keept
#     - merge from first: tags of the first and second table are merged (the first table tags override the second table tags)
#     - merge from second: tags of the first and second table are merged (the second table tags override the first table tags)
TableConcatOppositeTagOption = Literal["ignore", "keep first", "merge from first table"]


class TableConcatHelper:
    OPPOSITE_TAG_OPTIONS = Utils.get_literal_values(TableConcatOppositeTagOption)

    @classmethod
    def concat_table_rows(
        cls,
        tables: List[Table],
        column_tags_option: TableConcatOppositeTagOption = "ignore",
        fill_nan: Any = NaN,
    ) -> Table:
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
        :param fill_empty: value to replace NaN with. , defaults to NaN
        :type fill_empty: Any, optional
        :return: _description_
        :rtype: Table
        """

        concat_df: DataFrame = None
        row_tags: List[dict] = None
        column_tags: List[dict] = None

        for table in tables:
            if concat_df is None:
                concat_df = table.get_data()
                row_tags = table.get_row_tags()

                if (
                    column_tags_option == "merge from first table"
                    or column_tags_option == "keep first"
                ):
                    column_tags = cls._get_column_tags(concat_df, table)
            else:
                temp_df = concat([concat_df, table.get_data()])
                row_tags = row_tags + table.get_row_tags()

                if column_tags_option == "merge from first table":
                    current_table = Table(concat_df, column_tags=column_tags)
                    column_tags = cls._merge_column_tags(temp_df, current_table, table)

                concat_df = temp_df

        # add empty tag for each new column
        if column_tags_option == "keep first":
            tag_count = len(column_tags)
            dataframe_column_count = len(concat_df.columns)
            while tag_count < dataframe_column_count:
                column_tags.append({})
                tag_count += 1

        # fill empty values based on fill_empty
        # do nothing for NaN, it is already NaN
        if fill_nan is None:
            concat_df.replace({NaN: None}, inplace=True)
        elif isna(fill_nan):
            pass
        else:
            concat_df.fillna(fill_nan, inplace=True)

        return Table(concat_df, row_tags=row_tags, column_tags=column_tags)

    @classmethod
    def concat_table_columns(
        cls,
        tables: List[Table],
        row_tags_option: TableConcatOppositeTagOption = "ignore",
        fill_nan: Any = NaN,
    ) -> Table:
        """Concatenate two tables along the columns.
        The total number of columns will be the sum of the two tables. The total number of rows will depend if the two table
        have common rows (based on name).
        If the two table have the same row (based on name), the values of theses rows are concatenated starting from
        the first table into the same row.

        If a row doesn't exist in the other table, it will be concatenate with value provided in fill_nan.

        :param tables: list of tables to concatenate
        :type table: List[Table]
        :param row_tag_option: Option for the rows tags, defaults to 'ignore'
        :type row_tag_option: TableConcatOppositeTagOption, optional
        :param fill_empty: value to replace NaN with. , defaults to NaN
        :type fill_empty: Any, optional
        :return: _description_
        :rtype: Table
        """

        t_tables: List[Table] = []
        for table in tables:
            t_tables.append(table.transpose())
        result = cls.concat_table_rows(t_tables, row_tags_option, fill_nan)

        return result.transpose(infer_objects=True)

    @classmethod
    def _get_column_tags(cls, concat_df: DataFrame, table: Table) -> List[dict]:
        """For each concat_df columns take the tag from the table with same column name"""
        tag_list: List[dict] = []
        for column_name in concat_df:
            if table.column_exists(column_name):
                tag_list.append(table.get_column_tags_by_name(column_name))
            else:
                tag_list.append({})
        return tag_list

    @classmethod
    def _merge_column_tags(
        cls, concat_df: DataFrame, main_table: Table, second_table: Table
    ) -> List[dict]:
        """
        For each concat_df columns merge the tags from the main_table and second_table (with same column name),
        tags from main_table are preferred
        """

        tag_list: List[dict] = []
        for column_name in concat_df:
            tags = {}

            # get the tags from the second table
            if second_table.column_exists(column_name):
                tags = second_table.get_column_tags_by_name(column_name)

            # update the tags with the main table
            if main_table.column_exists(column_name):
                tags.update(main_table.get_column_tags_by_name(column_name))

            tag_list.append(tags)
        return tag_list
