# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
from typing import Type

from ...config.config_types import ConfigParams, ConfigSpecs
from ...config.param_spec import BoolParam, StrParam
from ...impl.file.file import File
from ...task.converter.exporter import ResourceExporter, exporter_decorator
from ...task.converter.importer import ResourceImporter, importer_decorator
from .json_dict import JSONDict

# ####################################################################
#
# Importer class
#
# ####################################################################


@importer_decorator(unique_name="JSONImporter", resource_type=JSONDict)
class JSONImporter(ResourceImporter):
    input_specs = {'file': File}

    config_specs: ConfigSpecs = {'file_format': StrParam(default_value=".json", short_description="File format")}

    async def import_from_path(self, file: File, params: ConfigParams, destination_type: Type[JSONDict]) -> JSONDict:
        with open(file.path, "r", encoding="utf-8") as f:
            json_data = destination_type()
            json_data.data = json.load(f)

        return json_data

        # ####################################################################
        #
        # Exporter class
        #
        # ####################################################################


@exporter_decorator("JSONExporter", resource_type=JSONDict)
class JSONExporter(ResourceExporter):
    pass
