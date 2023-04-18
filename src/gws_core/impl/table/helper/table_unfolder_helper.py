# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List

from numpy import NaN
from pandas import DataFrame, concat

from gws_core.tag.tag_helper import TagHelper

from ..table import Table


class TableUnfolderHelper:

    @classmethod
    def unfold_rows_by_tags(cls, table: Table, keys: List[str], tag_key_column_name: str) -> Table:
        """Create new column for each column and tags combinaison
        :param table: table to unfold
        :param table: Table
        :param keys: The tag keys
        :param keys: str
        :param tag_key_column_name: Name for the column tag key that receives the column name
        :param tag_key_column_name: str
        """

        t_t = table.transpose()
        result = cls.unfold_columns_by_tags(t_t, keys, tag_key_column_name)
        return result.transpose()

    ############################################## COLUMNS ######################################################

    @classmethod
    def unfold_columns_by_tags(cls, table: Table, keys: List[str], tag_key_row_name: str) -> Table:

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
                complete_tag = {**sub_table_row_tags[row_index], **tags, tag_key_row_name: row.name}
                complete_tags.append(complete_tag)
                row_index += 1

            row_tags.extend(complete_tags)

        table = Table(dataframe)
        table.set_all_row_tags(row_tags)
        return table
