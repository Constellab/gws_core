# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict, List

from pandas import DataFrame

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException

from ..impl.table.table import Table
from ..resource.r_field.primitive_r_field import StrRField
from ..resource.resource_decorator import resource_decorator

# ####################################################################
#
# Metadata class
#
# ####################################################################


@resource_decorator("MetadataTable",
                    human_name="MetadataTable",
                    short_description="Metadata table",
                    deprecated_since="0.4.7",
                    deprecated_message="Use Table instead",
                    hide=True)
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

    def get_sample_ids(self) -> list:
        return self.get_column_data(self.sample_id_column)

    def create_sub_table(
            self, dataframe: DataFrame, row_tags: List[Dict[str, str]],
            column_tags: List[Dict[str, str]]) -> 'Table':
        table: MetadataTable = super().create_sub_table(dataframe, row_tags, column_tags)
        if not self.sample_id_column in table.column_names:
            raise BadRequestException("The sample_id_column is required and must be selected")
        return table