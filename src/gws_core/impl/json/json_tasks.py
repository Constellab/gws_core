# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ...config.param_spec import BoolParam, StrParam
from ...task.exporter import TaskExporter, exporter_decorator
from ...task.importer import TaskImporter, importer_decorator
from ...task.task_decorator import task_decorator
from .json_dict import JSONDict

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator(unique_name="JSONImporter", resource_type=JSONDict)
class JSONImporter(TaskImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("FileExporter", resource_type=JSONDict)
class JSONExporter(TaskExporter):
    pass