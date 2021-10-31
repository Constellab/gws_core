
from ...config.param_spec import StrParam
from ...task.exporter import ResourceExporter, exporter_decorator
from ...task.importer import ResourceImporter, importer_decorator
from ...task.task_decorator import task_decorator
from .text import Text

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator(unique_name="TextImporter", resource_type=Text)
class TextImporter(ResourceImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator(unique_name="TextExporter", resource_type=Text)
class TextExporter(ResourceExporter):
    pass