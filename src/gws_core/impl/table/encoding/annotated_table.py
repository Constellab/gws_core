# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List

from ....resource.resource_decorator import resource_decorator
from ....task.converter.exporter import exporter_decorator
from ....task.converter.importer import import_from_path, importer_decorator
from ..table import Table
from ..table_tasks import TableExporter, TableImporter


@resource_decorator("AnnotatedTable")
class AnnotatedTable(Table):

    # -- S --

    def select_by_row_indexes(self, indexes: List[int]) -> 'AnnotatedTable':
        table = super().select_by_row_indexes(indexes)
        table = AnnotatedTable(data=table.get_data())
        return table

    def select_by_column_indexes(self, indexes: List[int]) -> 'AnnotatedTable':
        table = super().select_by_column_indexes(indexes)
        table = AnnotatedTable(data=table.get_data())
        return table

    def select_by_row_name(self, name_regex: str) -> 'AnnotatedTable':
        table = super().select_by_row_name(name_regex)
        table = AnnotatedTable(data=table.get_data())
        return table

    def select_by_column_name(self, name_regex: str) -> 'AnnotatedTable':
        table = super().select_by_column_name(name_regex)
        table = AnnotatedTable(data=table.get_data())
        return table

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("AnnotatedTableImporter", resource_type=AnnotatedTable)
class AnnotatedTableImporter(TableImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("AnnotatedTableExporter", resource_type=AnnotatedTable)
class AnnotatedTableExporter(TableExporter):
    pass
