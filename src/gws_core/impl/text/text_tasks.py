
import os
from typing import Type

from gws_core.impl.file.file_helper import FileHelper

from ...config.config_types import ConfigParams, ConfigSpecs
from ...config.param.param_spec import StrParam
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


@importer_decorator(unique_name="TextImporter", target_type=Text, supported_extensions=['txt'])
class TextImporter(ResourceImporter):

    config_specs: ConfigSpecs = {'encoding': StrParam(default_value='utf-8', short_description="Text encoding")}

    async def import_from_path(self, file: File, params: ConfigParams, target_type: Type[Text]) -> Text:
        try:
            with open(file.path, 'r+t', encoding=params.get_value('encoding', 'utf-8')) as fp:
                text = fp.read()
        except Exception as err:
            raise BadRequestException("Cannot import the text") from err

        return target_type(data=text)


# ####################################################################
#
# Exporter class
#
# ####################################################################


@exporter_decorator(unique_name="TextExporter", source_type=Text)
class TextExporter(ResourceExporter):

    config_specs: ConfigSpecs = {
        'file_name': StrParam(optional=True, short_description="Destination file name in the store"),
        'file_format': StrParam(optional=True, default_value=Text.DEFAULT_FILE_FORMAT, visibility=StrParam.PROTECTED_VISIBILITY, short_description="File format"),
        'encoding': StrParam(default_value='utf-8', visibility=StrParam.PROTECTED_VISIBILITY, short_description="Text encoding"),
    }

    async def export_to_path(self, resource: Text, dest_dir: str, params: ConfigParams, target_type: Type[File]) -> File:
        file_name = params.get_value('file_name', type(self)._human_name)
        file_format = FileHelper.clean_extension(params.get_value('file_format', Text.DEFAULT_FILE_FORMAT))
        file_path = os.path.join(dest_dir, file_name + '.' + file_format)

        try:
            with open(file_path, 'w+t', encoding=params.get_value('encoding', 'utf-8')) as fp:
                fp.write(resource._data)
        except Exception as err:
            raise BadRequestException("Cannot export the text") from err

        return File(file_path)
