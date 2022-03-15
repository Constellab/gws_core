# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from ....resource.resource_decorator import resource_decorator
from ....task.converter.exporter import exporter_decorator
from ....task.converter.importer import importer_decorator
from ..table import Table
from ..tasks.table_importer import TableImporter


@resource_decorator("EncodedTable")
class EncodedTable(Table):
    pass

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator("EncodedTableImporter", target_type=EncodedTable, supported_extensions=Table.ALLOWED_FILE_FORMATS)
class EncodedTableImporter(TableImporter):
    pass
