# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import os
from typing import Type

from ...config.config_types import ConfigParams, ConfigSpecs
from ...config.param_spec import BoolParam, StrParam
from ...task.converter.exporter import ResourceExporter, exporter_decorator
from ...task.converter.importer import ResourceImporter, importer_decorator
from .json_dict import JSONDict
from .json_file import JSONFile

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator(unique_name="JSONImporter", source_type=JSONFile, target_type=JSONDict)
class JSONImporter(ResourceImporter):
    config_specs: ConfigSpecs = {'file_format': StrParam(default_value=".json", short_description="File format")}

    async def import_from_path(self, file: JSONFile, params: ConfigParams, target_type: Type[JSONDict]) -> JSONDict:
        with open(file.path, "r", encoding="utf-8") as f:
            json_data = target_type()
            json_data.data = json.load(f)

        return json_data

        # ####################################################################
        #
        # Exporter class
        #
        # ####################################################################


@exporter_decorator("JSONExporter", source_type=JSONDict, target_type=JSONFile)
class JSONExporter(ResourceExporter):
    config_specs: ConfigSpecs = {
        'file_name': StrParam(optional=True, short_description="Destination file name in the store"),
        'file_format': StrParam(optional=True, default_value=".json", visibility=StrParam.PROTECTED_VISIBILITY, short_description="File format"),
        'prettify': BoolParam(default_value=False, visibility=BoolParam.PROTECTED_VISIBILITY, short_description="True to indent and prettify the JSON file, False otherwise")
    }

    async def export_to_path(self, resource: JSONDict, dest_dir: str, params: ConfigParams, target_type: Type[JSONFile]) -> JSONFile:
        file_name = params.get_value('file_name', type(self)._human_name)
        file_format = params.get_value('file_format', '.json')
        file_path = os.path.join(dest_dir, file_name+file_format)

        with open(file_path, "w", encoding="utf-8") as f:
            if params.get_value('prettify', False):
                json.dump(resource.data, f, indent=4)
            else:
                json.dump(resource.data, f)

        return JSONFile(file_path)
