
import os
from typing import Type

from ...config.config_types import ConfigParams, ConfigSpecs
from ...config.param_spec import StrParam
from ...core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ...task.converter.exporter import ResourceExporter, exporter_decorator
from ...task.converter.importer import ResourceImporter, importer_decorator
from ..file.file import File
from .text import Text

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator(unique_name="TextImporter", resource_type=Text)
class TextImporter(ResourceImporter):
    input_specs = {'file': File}

    config_specs: ConfigSpecs = {'encoding': StrParam(default_value='utf-8', short_description="Text encoding")}

    async def import_from_path(self, file: File, params: ConfigParams, destination_type: Type[Text]) -> Text:
        try:
            with open(file.path, 'r+t', encoding=params.get_value('encoding', 'utf-8')) as fp:
                text = fp.read()
        except Exception as err:
            raise BadRequestException("Cannot import the text") from err

        return destination_type(data=text)


# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator(unique_name="TextExporter", resource_type=Text)
class TextExporter(ResourceExporter):
    output_specs = {"file": File}

    config_specs: ConfigSpecs = {
        'file_name': StrParam(default_value='file.txt', short_description="Destination file name in the store"),
        'encoding': StrParam(default_value='utf-8', short_description="Text encoding"),
        'file_store_id': StrParam(optional=True, short_description="ID of the file_store where the file must be exported"),
    }

    async def export_to_path(self, resource: Text, dest_dir: str, params: ConfigParams) -> File:
        file_path = os.path.join(dest_dir, params.get_value('file_name', 'file.txt'))

        try:
            with open(file_path, 'w+t', encoding=params.get_value('encoding', 'utf-8')) as fp:
                fp.write(resource._data)
        except Exception as err:
            raise BadRequestException("Cannot export the text") from err

        return File(file_path)
