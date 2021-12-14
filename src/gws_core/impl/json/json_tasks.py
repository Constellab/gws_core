# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from ...config.param_spec import BoolParam, StrParam
from ...task.converter.exporter import ResourceExporter, exporter_decorator
from ...task.converter.importer import ResourceImporter, importer_decorator
from ...task.task_decorator import task_decorator
from .json_dict import JSONDict

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator(unique_name="JSONImporter", resource_type=JSONDict)
class JSONImporter(ResourceImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator("JSONExporter", resource_type=JSONDict)
class JSONExporter(ResourceExporter):
    pass
