
from ...config.param_spec import StrParam
from ...task.exporter import TaskExporter, exporter_decorator
from ...task.importer import TaskImporter, importer_decorator
from ...task.task_decorator import task_decorator
from ..file.file_uploader import FileDumper, FileLoader
from .text import Text

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator(unique_name="TextImporter", resource_type=Text)
class TextImporter(TaskImporter):
    pass

# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator(unique_name="TextExporter", resource_type=Text)
class TextExporter(TaskExporter):
    pass

# ####################################################################
#
# Loader class
#
# ####################################################################


@task_decorator(unique_name="TextLoader")
class TextLoader(FileLoader):
    input_specs = {}
    output_specs = {'data': Text}
    config_specs = {
        'file_path': StrParam(optional=True, short_description="Location of the file to import"),
        'encoding': StrParam(default_value='utf-8', short_description="Text encoding")
    }

# ####################################################################
#
# Dumper class
#
# ####################################################################


@task_decorator(unique_name="TextDumper")
class TextDumper(FileDumper):
    input_specs = {'data': Text}
    output_specs = {}
    config_specs = {
        'file_path': StrParam(optional=True, short_description="Destination of the exported file"),
        'encoding': StrParam(default_value='utf-8', short_description="Text encoding")
    }
