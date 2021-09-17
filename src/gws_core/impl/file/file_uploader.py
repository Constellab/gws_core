# ####################################################################
#
# Uploader class
#
# ####################################################################

import copy
import os
from pathlib import Path
from typing import Type

from ...config.param_spec import StrParam
from ...config.config_types import ConfigParams
from ...core.utils.utils import Utils
from ...resource.resource import Resource
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from .file import File
from .local_file_store import LocalFileStore

# ####################################################################
#
# Importer class
#
# ####################################################################


@task_decorator("FileImporter")
class FileImporter(Task):
    input_specs = {'file': File}
    output_specs = {"data": Resource}
    config_specs = {'file_format': StrParam(optional=True, description="File format"), 'output_type': {StrParam(
        default_value="", description="The output file type. If defined, it is used to automatically format data output")}}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        inport_name = list(self.input_specs.keys())[0]
        outport_name = list(self.output_specs.keys())[0]
        file: File = inputs[inport_name]

        model_t: Type[Resource] = None
        if params.value_is_set("output_type"):
            out_t = params.get_value("output_type")
            if out_t:
                model_t = Utils.get_model_type(out_t)

        if not model_t:
            model_t = self.get_default_output_spec_type(outport_name)

        params = copy.deepcopy(params)
        resource = model_t.import_from_path(file.path, **params)
        return {outport_name: resource}


# ####################################################################
#
# Exporter class
#
# ####################################################################
@ task_decorator("FileExporter")
class FileExporter(Task):
    """
    File exporter. The file is writen in a file store
    """

    input_specs = {"data": Resource}
    output_specs = {'file': File}
    config_specs = {
        'file_name': StrParam(default_value='file', description="Destination file name in the store"),
        'file_format': StrParam(optional=True, description="File format"),
        'file_store_uri': StrParam(optional=True, description="URI of the file_store where the file must be exported"),
    }

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        file_store: LocalFileStore
        if params.value_is_set('file_store_uri'):
            file_store = LocalFileStore.get_by_uri_and_check(params.get('file_store_uri'))
        else:
            file_store = LocalFileStore.get_default_instance()

        inport_name = list(self.input_specs.keys())[0]
        outport_name = list(self.output_specs.keys())[0]
        filename = params.get_value("file_name")
        file_type: Type[File] = self.get_default_output_spec_type("file")
        file: File = file_store.create_file(file_name=filename, file_type=file_type)

        if not os.path.exists(file.dir):
            os.makedirs(file.dir)

        params = copy.deepcopy(params)
        if "file_name" in params:
            del params["file_name"]

        resource: Resource = inputs[inport_name]
        resource.export_to_path(file.path, **params)
        return {outport_name: file}

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
        'file_path': StrParam(optional=True, description="Location of the file to import"),
        'file_format': StrParam(optional=True, description="File format"),
        'output_type':
        StrParam(default_value="",
                 description="The output file type. If defined, it is used to automatically format data output"), }

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
        'file_path': StrParam(optional=True, description="Destination of the exported file"),
        'file_format': StrParam(optional=True, description="File format"),
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
