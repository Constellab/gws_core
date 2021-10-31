
from ...config.param_spec import BoolParam, IntParam, StrParam, ListParam
from ...task.exporter import ResourceExporter, exporter_decorator
from ...task.importer import ResourceImporter, importer_decorator
from ...task.task_decorator import task_decorator
from ..file.file import File
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
