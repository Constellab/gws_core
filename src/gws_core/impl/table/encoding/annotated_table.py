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
from ..table_file import TableFile
from ..tasks.table_exporter import TableExporter
from ..tasks.table_importer import TableImporter


@resource_decorator("AnnotatedTable")
class AnnotatedTable(Table):
    """
    Table with key-value columns names
    """

    pass

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("AnnotatedTableImporter", source_type=TableFile, target_type=AnnotatedTable)
class AnnotatedTableImporter(TableImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("AnnotatedTableExporter", source_type=AnnotatedTable, target_type=TableFile)
class AnnotatedTableExporter(TableExporter):
    pass
