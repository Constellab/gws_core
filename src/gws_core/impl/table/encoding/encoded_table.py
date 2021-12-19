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
from ..table_tasks import TableExporter, TableImporter


@resource_decorator("EncodedTable")
class EncodedTable(Table):
    pass

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("EncodedTableImporter", source_type=TableFile, target_type=EncodedTable)
class EncodedTableImporter(TableImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("EncodedTableExporter", source_type=EncodedTable, target_type=TableFile)
class EncodedTableExporter(TableExporter):
    pass
