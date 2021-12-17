# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core.impl.file.file import File

from ....resource.resource_decorator import resource_decorator
from ....task.converter.exporter import exporter_decorator
from ....task.converter.importer import importer_decorator
from ..table import Table
from ..table_tasks import TableExporter, TableImporter


@resource_decorator("EncodedTable")
class EncodedTable(Table):

    # -- S --

    def select_by_row_indexes(self, indexes: List[int]) -> 'EncodedTable':
        table = super().select_by_row_indexes(indexes)
        table = EncodedTable(data=table.get_data())
        return table

    def select_by_column_indexes(self, indexes: List[int]) -> 'EncodedTable':
        table = super().select_by_column_indexes(indexes)
        table = EncodedTable(data=table.get_data())
        return table

    def select_by_row_name(self, name_regex: str) -> 'EncodedTable':
        table = super().select_by_row_name(name_regex)
        table = EncodedTable(data=table.get_data())
        return table

    def select_by_column_name(self, name_regex: str) -> 'EncodedTable':
        table = super().select_by_column_name(name_regex)
        table = EncodedTable(data=table.get_data())
        return table

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("EncodedTableImporter", target_type=EncodedTable)
class EncodedTableImporter(TableImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("EncodedTableExporter", source_type=EncodedTable)
class EncodedTableExporter(TableExporter):
    pass
