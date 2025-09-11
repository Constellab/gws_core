

from typing import Any, Dict, List

from gws_core.tag.tag_helper import TagHelper
from numpy import NaN
from pandas import DataFrame, concat

from ..table import Table


class TableUnfolderHelper:

    @classmethod
    def unfold_rows_by_tags(
            cls, table: Table, keys: List[str],
            tag_key_column_original_name: str = 'column_original_name') -> Table:
        """Create new column for each column and tags combinaison
        Then it tags the column with the original column name

        :param table: table to unfold
        :param table: Table
        :param keys: The tag keys
        :param keys: str
        :param tag_key_column_name: Key of new tag that will be added to the new unfolded columns containing the original column name.
                                    This is useful to know which original column was used to create the new unfolded column.
        :param tag_key_column_name: str
        """

        t_t = table.transpose()
        result = cls.unfold_columns_by_tags(t_t, keys, tag_key_column_original_name)
        return result.transpose()

    ############################################## COLUMNS ######################################################

    @classmethod
    def unfold_columns_by_tags(
            cls, table: Table, keys: List[str],
            tag_key_row_original_name: str = 'row_original_name') -> Table:
        """Create new row for each row and tags combinaison
        Then it tags the row with the original row name

        :param table: table to unfold
        :param table: Table
        :param keys: The tag keys
        :param keys: str
        :param tag_key_row_name: Key of new tag that will be added to the new unfolded rows containing the original row name.
                                 This is useful to know which original row was used to create the new unfolded row.
        :param tag_key_row_name: str
        """

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

            row_index = 0
            complete_tags: List[dict] = []
            sub_table_row_tags: List[dict] = sub_table.get_row_tags()
            for _, row in df.iterrows():
                name = f"{row.name}_{tag_values}"

                # if the new row have fewer column than dataframe, append NaN
                values: List[Any] = row.values.tolist()
                column_diff = len(dataframe.columns) - len(values)
                if column_diff > 0:
                    values.extend([NaN] * column_diff)

                row_df = DataFrame([values], index=[name])

                dataframe = concat([dataframe, row_df], sort=True)

                # create the tags for the new row
                # get the row tags before the unfolder,
                # append tags that are used to unfold and append the row name as tag
                complete_tag = {**sub_table_row_tags[row_index], **tags, tag_key_row_original_name: row.name}
                complete_tags.append(complete_tag)
                row_index += 1

            row_tags.extend(complete_tags)

        table = Table(dataframe)
        table.set_all_row_tags(row_tags)
        return table

    ############################################### USING ROW AND COLUMNS ######################################################

    def unfold_by_rows(
            self, table: Table, rows: List[str],
            tag_key_row_original_name: str = 'row_original_name') -> Table:
        """Create new column for each column and rows combinaison
        Then it tags the column with the original column name

        :param table: table to unfold
        :param table: Table
        :param rows: The rows reference to unfold by
        :param rows: str
        :param tag_key_column_name: Key of new tag that will be added to the new unfolded columns containing the original column name.
                                    This is useful to know which original column was used to create the new unfolded column.
        :param tag_key_column_name: str
        """

        for row in rows:
            if row not in table.get_data().index:
                raise Exception(f"Row {row} not found in table.")

            table.extract_row_values_to_column_tags(row, delete_row=True)

        return self.unfold_columns_by_tags(table, rows, tag_key_row_original_name)

    def unfold_by_columns(
            self, table: Table, columns: List[str],
            tag_key_column_original_name: str = 'column_original_name') -> Table:
        """Create new row for each row and columns combinaison
        Then it tags the row with the original row name

        :param table: table to unfold
        :param table: Table
        :param columns: The columns reference to unfold by
        :param columns: str
        :param tag_key_row_name: Key of new tag that will be added to the new unfolded
                                    rows containing the original row name.
                                    This is useful to know which original row was used to create the new unfolded row.
        :param tag_key_row_name: str
        """

        for column in columns:
            if column not in table.get_data().columns:
                raise Exception(f"Column {column} not found in table.")

            table.extract_column_values_to_row_tags(column, delete_column=True)

        return self.unfold_rows_by_tags(table, columns, tag_key_column_original_name)
