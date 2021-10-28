# ####################################################################
#
# Uploader class
#
# ####################################################################

import copy
import os
from pathlib import Path
from typing import Type

from ...config.config_types import ConfigParams
from ...config.param_spec import StrParam
from ...core.utils.utils import Utils
from ...resource.resource import Resource
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs

# ####################################################################
#
# Loader class
#
# ####################################################################


@ task_decorator("FileLoader")
class FileLoader(Task):
    input_specs = {}
    output_specs = {"data": Resource}
    config_specs = {
        'file_path': StrParam(optional=True, short_description="Location of the file to import"),
        'file_format': StrParam(optional=True, short_description="File format"),
        'output_type':
        StrParam(
            default_value="",
            short_description="The output file type. If defined, it is used to automatically format data output"), }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        outport_name = list(self.output_specs.keys())[0]
        file_path = params.get_value("file_path")

        model_t: Type[Resource] = None
        if params.value_is_set("output_type"):
            out_t = params.get_value("output_type")
            if out_t:
                model_t = Utils.get_model_type(out_t)

        if not model_t:
            model_t = self.get_default_output_spec_type(outport_name)

        params = copy.deepcopy(params)
        if "file_path" in params:
            del params["file_path"]

        resource = model_t.import_from_path(file_path, **params)
        return {outport_name: resource}

# ####################################################################
#
# Dumper class
#
# ####################################################################


@ task_decorator("FileDumper")
class FileDumper(Task):
    """
    Generic data exporter
    """

    input_specs = {"data": Resource}
    output_specs = {}
    config_specs = {
        'file_path': StrParam(optional=True, short_description="Destination of the exported file"),
        'file_format': StrParam(optional=True, short_description="File format"),
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        file_path = params.get_value("file_path")
        inport_name = list(self.input_specs.keys())[0]
        resource: Resource = inputs[inport_name]

        p = Path(file_path)
        parent_dir = p.parent
        if not os.path.exists(parent_dir):
            os.makedirs(parent_dir)

        params = copy.deepcopy(params)
        if "file_path" in params:
            del params["file_path"]

        resource.export_to_path(file_path, **params)
