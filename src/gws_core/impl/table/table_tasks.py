# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ...task.converter.exporter import ResourceExporter, exporter_decorator
from ...task.converter.importer import ResourceImporter, importer_decorator
from .table import Table

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator(unique_name="TableImporter", resource_type=Table)
class TableImporter(ResourceImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator(unique_name="TableExporter", resource_type=Table)
class TableExporter(ResourceExporter):
    pass
