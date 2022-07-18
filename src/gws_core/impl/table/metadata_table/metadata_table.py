# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.impl.table.helper.dataframe_filter_helper import \
    DataframeFilterName
from gws_core.impl.table.table_types import TableMeta
from pandas import DataFrame

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

    def get_sample_ids(self) -> list:
        return self.get_column_as_list(self.sample_id_column)

    def create_sub_table(self, dataframe: DataFrame, meta: TableMeta) -> 'Table':
        table: MetadataTable = super().create_sub_table(dataframe, meta)
        if not self.sample_id_column in table.column_names:
            raise BadRequestException("The sample_id_column is required and must be selected")
        return table
