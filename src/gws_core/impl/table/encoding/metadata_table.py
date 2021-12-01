# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

import pandas
from pandas import DataFrame

from ....config.config_types import ConfigParams
from ....config.param_spec import BoolParam, IntParam, ListParam, StrParam
from ....core.exception.exceptions import BadRequestException
from ....impl.file.file import File
from ....resource.r_field import StrRField
from ....resource.resource import Resource
from ....resource.resource_decorator import resource_decorator
from ....resource.view_decorator import view
from ....task.exporter import export_to_path, exporter_decorator
from ....task.importer import import_from_path, importer_decorator
from ..table import Table
from ..table_tasks import TableExporter, TableImporter

# ####################################################################
#
# Metadata class
#
# ####################################################################

SAMPLE_COLUMN = "sample"
importer_specs = TableImporter.config_specs
del importer_specs["index_columns"]


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

    _KEY_VALUE_SEPARATOR = ":"
    _TOKEN_SEPARATOR = "|"
    _REPLACEMENT_CHAR = "_"

    SAMPLE_COLUMN = SAMPLE_COLUMN
    sample_column: str = StrRField(default_value=SAMPLE_COLUMN)

    # -- F --

    @classmethod
    def _clear_value(cls, val):
        val = f"{val}".replace(cls._KEY_VALUE_SEPARATOR, cls._REPLACEMENT_CHAR)
        val = val.replace(cls._TOKEN_SEPARATOR, cls._REPLACEMENT_CHAR)
        return val

    @classmethod
    def _format_key_value(cls, key, value) -> str:
        key = cls._clear_value(key)
        value = cls._clear_value(value)
        return f"{key}{cls._KEY_VALUE_SEPARATOR}{value}"

    # -- G --

    def get_sample_data(self) -> list:
        return self._data.index.to_list()

    # -- I --

    @classmethod
    @import_from_path(specs=TableImporter.config_specs)
    def import_from_path(cls, file: File, params: ConfigParams) -> 'MetadataTable':
        """
        Import from a repository

        :param file: The file to import
        :type file: `File`
        :param params: The config params
        :type params: `ConfigParams`
        :returns: the parsed MetadataTable data
        :rtype: MetadataTable
        """

        params["index_colums"] = params.get_value("index_colums", [0])  # use the first colum by default
        csv_table = super().import_from_path(file, params)
        return csv_table

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
        name_regex = self._format_key_value(key, value)
        table = super().select_by_column_name(".*" + name_regex + ".*")
        table = MetadataTable(data=table.get_data())
        return table

# ####################################################################
#
# Importer class
#
# ####################################################################


@ importer_decorator("MetadataTableImporter", resource_type=MetadataTable)
class MetadataTableImporter(TableImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@ exporter_decorator("MetadataTableExporter", resource_type=MetadataTable)
class MetadataTableExporter(TableExporter):
    pass
