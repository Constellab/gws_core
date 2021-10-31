
from ...config.param_spec import BoolParam, IntParam, StrParam, ListParam
from ...task.exporter import TaskExporter, exporter_decorator
from ...task.importer import TaskImporter, importer_decorator
from ...task.task_decorator import task_decorator
from ..file.file import File
from .table import Table

# ####################################################################
#
# Importer class
#
# ####################################################################

@importer_decorator(unique_name="TableImporter", resource_type=Table)
class TableImporter(TaskImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################

@exporter_decorator(unique_name="TableExporter", resource_type=Table)
class TableExporter(TaskExporter):
    pass
