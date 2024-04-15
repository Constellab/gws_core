

import json
import os
from typing import Type

from gws_core.core.utils.utils import Utils
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.folder import Folder
from gws_core.impl.file.fs_node import FSNode
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_manager import TypingManager

from ...config.config_params import ConfigParams
from ...config.config_types import ConfigSpecs
from ...config.param.param_spec import StrParam
from ...impl.file.file import File
from ...impl.file.file_store import FileStore
from ...impl.file.local_file_store import LocalFileStore
from ...io.io_specs import InputSpecs, OutputSpecs
from ...resource.resource import Resource
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs


@task_decorator(unique_name="WriteToJsonFile", human_name="Write to file",
                short_description="Simple task to write a resource json data to a file in local store",
                style=File.copy_style())
class WriteToJsonFile(Task):
    input_specs: InputSpecs = InputSpecs({'resource': InputSpec(Resource)})
    output_specs: OutputSpecs = OutputSpecs({'file': OutputSpec(File)})
    config_specs: ConfigSpecs = {'filename': StrParam(
        short_description='Name of the file')}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        file_store: FileStore = LocalFileStore.get_default_instance()

        file: File = file_store.create_empty_file(
            params.get_value('filename') + '.json')

        resource: Resource = inputs['resource']
        file.write(json.dumps(resource.view_as_json(
            ConfigParams()).to_dto(ConfigParams()).to_json_dict()))

        return {"file": file}


@task_decorator(unique_name="FsNodeExtractor", human_name="Fs node extractor",
                short_description="Extract a sub file or folder from a folder to generated a new resource")
class FsNodeExtractor(Task):
    """Task to extract a file from a folder to create a resource

    :param Task: _description_
    :type Task: _type_
    :return: _description_
    :rtype: _type_
    """

    input_specs = InputSpecs({"source": InputSpec(Folder)})
    output_specs = OutputSpecs({"target": OutputSpec(FSNode)})

    # Override the config_spec to define custom spec for the importer
    config_specs: ConfigSpecs = {
        "fs_node_path": StrParam(), "fs_node_typing_name": StrParam()}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # retrieve resource type
        _type: Type[FSNode] = TypingManager.get_and_check_type_from_name(
            params.get('fs_node_typing_name'))

        path: str = params.get('fs_node_path')

        folder: Folder = inputs['source']

        full_path = os.path.join(folder.path, path)

        # check the resource type is correct
        if FileHelper.is_dir(full_path) and not Utils.issubclass(_type, Folder):
            raise Exception('The provided type is not a folder')
        if FileHelper.is_file(full_path) and not Utils.issubclass(_type, File):
            raise Exception('The provided type is not a file')

        fs_node: FSNode = _type(full_path)
        # mark the node as symbolic link. The node will not be deleted when resource is deleted
        fs_node.is_symbolic_link = True

        return {'target': fs_node}
