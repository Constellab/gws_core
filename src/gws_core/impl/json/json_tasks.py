

import json
import os
from typing import Type

import simplejson

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper

from ...config.config_params import ConfigParams
from ...config.config_types import ConfigSpecs
from ...config.param.param_spec import BoolParam, StrParam
from ...task.converter.exporter import ResourceExporter, exporter_decorator
from ...task.converter.importer import ResourceImporter, importer_decorator
from .json_dict import JSONDict


@importer_decorator(unique_name="JSONImporter", target_type=JSONDict, supported_extensions=['json'])
class JSONImporter(ResourceImporter):
    config_specs: ConfigSpecs = {'file_format': StrParam(default_value="json", short_description="File format")}

    def import_from_path(self, source: File, params: ConfigParams, target_type: Type[JSONDict]) -> JSONDict:
        if source.is_empty():
            raise BadRequestException(GWSException.EMPTY_FILE.value, unique_code=GWSException.EMPTY_FILE.name,
                                      detail_args={'filename': source.path})

        with open(source.path, "r", encoding="utf-8") as f:
            json_data = target_type()
            json_data.data = json.load(f)

        return json_data


@exporter_decorator("JSONExporter", source_type=JSONDict)
class JSONExporter(ResourceExporter):
    config_specs: ConfigSpecs = {
        'file_name': StrParam(optional=True, short_description="Destination file name in the store"),
        'file_format':
        StrParam(
            optional=True, default_value="json", visibility=StrParam.PROTECTED_VISIBILITY,
            short_description="File format"),
        'prettify':
        BoolParam(
            default_value=False, visibility=BoolParam.PROTECTED_VISIBILITY,
            short_description="True to indent and prettify the JSON file, False otherwise")}

    def export_to_path(self, source: JSONDict, dest_dir: str, params: ConfigParams, target_type: Type[File]) -> File:
        file_name = params.get_value('file_name', type(self)._human_name)
        file_format = FileHelper.clean_extension(params.get_value('file_format', 'json'))
        file_path = os.path.join(dest_dir, file_name + '.' + file_format)

        with open(file_path, "w", encoding="utf-8") as file:
            if params.get_value('prettify', False):
                simplejson.dump(source.data, file, indent=4, ignore_nan=True, iterable_as_array=True, default=str)
            else:
                simplejson.dump(source.data, file, ignore_nan=True, iterable_as_array=True, default=str)

        return File(file_path)
