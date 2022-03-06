# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core.impl.table.table_file import TableFile

from ....resource.r_field import StrRField
from ....resource.resource_decorator import resource_decorator
from ..table import Table

# ####################################################################
#
# Metadata class
#
# ####################################################################


@resource_decorator("MetadataTable",
                    human_name="MetadataTable",
                    short_description="Metadata table")
class MetadataTable(Table):
    """
    Represents a sample metadata table

    Metadata table contain categorical `key, value` data used to annotated sample tables.

    For example:

    ```
    -------------------------------------------
    sample_id   | key1    |  key2   | key3
    -------------------------------------------
    id1         | value1  |  value3 | value5
    id2         | value2  |  value4 | value6
    -------------------------------------------
    ```

    The annotated table will be such as the column name `name1` will be converted to `key1:value1|key2:value2|key3:value3`
    """

    DEFAULT_SAMPLE_ID_COLUMN = "sample_id"

    sample_id_column: str = StrRField(default_value=DEFAULT_SAMPLE_ID_COLUMN)

    # -- F --

    def get_sample_ids(self, rtype='list') -> ('DataFrame', list):
        return self.get_column(self.sample_id_column, rtype)

    # -- G --

    # -- S --

    def select_by_row_positions(self, positions: List[int]) -> 'MetadataTable':
        table = super().select_by_row_positions(positions)
        table.sample_id_column = self.sample_id_column
        return table

    def select_by_column_positions(self, positions: List[int], check_integrity: bool = True) -> 'MetadataTable':
        table = super().select_by_column_positions(positions)
        if not self.sample_id_column in table.column_names:
            raise BadRequestException("The sample_id_column is required and must be selected")
        table.sample_id_column = self.sample_id_column
        return table

    def select_by_row_names(self, names: List[str], use_regex=False) -> 'MetadataTable':
        table = super().select_by_row_names(names, use_regex)
        table.sample_id_column = self.sample_id_column
        return table

    def select_by_column_names(self, names: List[str], use_regex=False) -> 'MetadataTable':
        table = super().select_by_column_names(names, use_regex)
        if not self.sample_id_column in table.column_names:
            raise BadRequestException("The sample_id_column is required and must be selected")
        table.sample_id_column = self.sample_id_column
        return table


@resource_decorator("MetadataTableFile",
                    human_name="MetadataTable file",
                    short_description="Table file of metadata")
class MetadataTableFile(TableFile):
    pass
