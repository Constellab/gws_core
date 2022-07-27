# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, Dict, List, Literal

from gws_core.core.utils.numeric_helper import NumericHelper
from gws_core.core.utils.utils import Utils
from gws_core.impl.table.table import Table
from numpy import NaN

TableTagExtractType = Literal['char', 'numeric']


class TableTagExtractorHelper:

    TAG_EXTRACT_TYPES: List[str] = Utils.get_literal_values(TableTagExtractType)

    @classmethod
    def extract_row_tags(cls, table: Table, key: str,
                         tag_values_type: TableTagExtractType = 'char', new_column_name: str = None) -> Table:
        """Extract the row tags to a new column

        :param table: table
        :type table: Table
        :param key: key of the tag to extract values from
        :type key: str
        :param tag_values_type: type of the tag values. It numeric the tag values are converted to float, defaults to 'char'
        :type tag_values_type: TableTagExtractType, optional
        :param new_column_name: name of the new column that will contains tag values. If none, tag key is used as name, defaults to None
        :type new_column_name: str, optional
        :return: _description_
        :rtype: Table
        """
        table = table.clone()

        # create a new column name
        if new_column_name is None:
            new_column_name = table.generate_new_column_name(key)
        else:
            new_column_name = table.generate_new_column_name(new_column_name)

        tags: List[Dict[str, str]] = table.get_row_tags()

        tags_values = [tag.get(key) for tag in tags]
        converted_tags: List[Any]

        if tag_values_type == 'numeric':
            converted_tags = NumericHelper.list_to_float(tags_values, default_value=NaN)
        else:
            converted_tags = tags_values

        table.add_column(new_column_name, converted_tags)

        return table

    @classmethod
    def extract_column_tags(cls, table: Table, key: str,
                            tag_values_type: TableTagExtractType = 'char', new_row_name: str = None) -> Table:
        """Extract the column tags to a new row

        :param table: table
        :type table: Table
        :param key: key of the tag to extract values from
        :type key: str
        :param tag_values_type: type of the tag values. It numeric the tag values are converted to float, defaults to 'char'
        :type tag_values_type: TableTagExtractType, optional
        :param new_row_name: name of the new row that will contains tag values. If none, tag key is used as name, defaults to None
        :type new_row_name: str, optional
        :return: _description_
        :rtype: Table
        """

        t_table = table.transpose()

        result = cls.extract_row_tags(t_table, key, tag_values_type, new_row_name)

        return result.transpose()
