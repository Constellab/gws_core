# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Type

from ....config.config_types import ConfigParams
from ....impl.file.file import File
from ....resource.resource_decorator import resource_decorator
from ....task.converter.exporter import exporter_decorator
from ....task.converter.importer import importer_decorator
from ..table import Table
from ..table_tasks import TableExporter, TableImporter

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
    Represents a metadata table

    Metadata table contain categorical `key, value` data used to annotated sample tables.

    For example:

    ```
    -------------------------------------------
    sample   | key1    |  key2   | key3
    -------------------------------------------
    name1    | value1  |  value3 | value5
    name2    | value2  |  value4 | value6
    -------------------------------------------
    ```

    The annotated table will be such as the column name `name1` will be converted to `key1:value1|key2:value2|key3:value3`
    """

    KEY_VALUE_SEPARATOR = ":"
    TOKEN_SEPARATOR = "|"
    REPLACEMENT_CHAR = "_"

    # -- F --

    @classmethod
    def _clear_value(cls, val):
        val = f"{val}".replace(cls.KEY_VALUE_SEPARATOR, cls.REPLACEMENT_CHAR)
        val = val.replace(cls.TOKEN_SEPARATOR, cls.REPLACEMENT_CHAR)
        return val

    @classmethod
    def format_token(cls, key, value) -> str:
        key = cls._clear_value(key)
        value = cls._clear_value(value)
        return f"{key}{cls.KEY_VALUE_SEPARATOR}{value}"

    # -- G --

    def get_sample_data(self) -> list:
        return self._data.index.to_list()

    # -- S --

    def select_by_row_indexes(self, indexes: List[int]) -> 'MetadataTable':
        table = super().select_by_row_indexes(indexes)
        table = MetadataTable(data=table.get_data())
        return table

    def select_by_column_indexes(self, indexes: List[int]) -> 'MetadataTable':
        table = super().select_by_column_indexes(indexes)
        table = MetadataTable(data=table.get_data())
        return table

    def select_by_row_name(self, name_regex: str) -> 'MetadataTable':
        table = super().select_by_row_name(name_regex)
        table = MetadataTable(data=table.get_data())
        return table

    def select_by_column_name(self, name_regex: str) -> 'MetadataTable':
        table = super().select_by_column_name(name_regex)
        table = MetadataTable(data=table.get_data())
        return table

    def select_by_key_value(self, key: str, value: str) -> 'MetadataTable':
        name_regex = self.format_token(key, value)
        table = super().select_by_column_name(".*" + name_regex + ".*")
        table = MetadataTable(data=table.get_data())
        return table

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("MetadataTableImporter", target_type=MetadataTable)
class MetadataTableImporter(TableImporter):

    async def import_from_path(self, file: File, params: ConfigParams, target_type: Type[MetadataTable]) -> MetadataTable:
        params["index_colums"] = params.get_value("index_colums", [0])  # use the first colum by default
        csv_table = await super().import_from_path(file, params, target_type)
        return csv_table


# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("MetadataTableExporter", source_type=MetadataTable)
class MetadataTableExporter(TableExporter):
    pass
