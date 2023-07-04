# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import json
import os
from typing import Type

from gws_core.core.classes.file_downloader import FileDownloader
from gws_core.core.utils.settings import Settings
from gws_core.core.utils.utils import Utils
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.folder import Folder
from gws_core.impl.file.fs_node import FSNode
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_manager import TypingManager

from ...config.config_types import ConfigParams, ConfigSpecs
from ...config.param.param_spec import BoolParam, StrParam
from ...impl.file.file import File
from ...impl.file.file_store import FileStore
from ...impl.file.local_file_store import LocalFileStore
from ...io.io_specs import InputSpecs, OutputSpecs
from ...resource.resource import Resource
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs


@task_decorator(unique_name="WriteToJsonFile", human_name="Write to file",
                short_description="Simple task to write a resource json data to a file in local store")
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
            ConfigParams()).to_dict(ConfigParams())))

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
        _type: Type[FSNode] = TypingManager.get_type_from_name(
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


@task_decorator(unique_name="FileDownloader", human_name="File downloader",
                short_description="Download a file from a remote url to the lab and create a resource with the file")
class FileDownloaderTask(Task):

    input_specs = InputSpecs({})
    output_specs = OutputSpecs({"fs_node": OutputSpec(FSNode)})

    config_specs: ConfigSpecs = {
        "file_url": StrParam(human_name="File url"),
        "filename": StrParam(human_name="Name of the file/folder once downloaded"),
        "decompress_file": BoolParam(human_name="Unzip downloaded file in a folder"),
    }

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        destination = Settings.get_instance().make_temp_dir()
        file_downloader = FileDownloader(destination, self.message_dispatcher)

        file_path = file_downloader.download_file_if_missing(
            params.get('file_url'),
            params.get('filename'),
            decompress_file=params.get('decompress_file')
        )

        if FileHelper.is_dir(file_path):
            return {"fs_node": Folder(file_path)}
        else:
            return {"fs_node": File(file_path)}
