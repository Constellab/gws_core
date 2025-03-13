

import os
from typing import List

from gws_core.config.config_types import ConfigSpecs
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import StrParam
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.file.folder import Folder
from gws_core.impl.file.fs_node import FSNode
from gws_core.io.dynamic_io import DynamicInputs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.resource.resource_set.resource_list import ResourceList

from ...config.config_params import ConfigParams
from ...io.io_specs import InputSpecs, OutputSpecs
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs


@task_decorator(unique_name="CreateFolderFromFile", human_name="Create folder from files",
                short_description="Create a folder from a list of files or folders.")
class CreateFolderFromFiles(Task):
    """
    Create a folder from a list of files or folders.
    Provide a list of files or folders as input and the task will create
    a folder containing the files or folders.

    The input file and folder are copied to the new folder.

    **Configuration**:
    List of filenames to use for the files or folders in the input list.
    If not provided, the original filenames will be used.
    The filenames must be provided in the same order as the input list.

    Ex: The second filename overide the name of the second input file or folder.
    """

    input_specs: InputSpecs = DynamicInputs(
        additionnal_port_spec=InputSpec(FSNode, human_name="File or folder"))
    output_specs = OutputSpecs({'folder': OutputSpec(Folder, human_name='Folder')})

    config_specs: ConfigSpecs = {
        'folder_name': StrParam(human_name="Output folder name", short_description="Name of the folder to create", optional=True),
        'filenames': ParamSet({'filename': StrParam(
            human_name="Filename", short_description="Overide the file or folder name at this index", optional=True)}, optional=True)}

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        temp_dir: str = None

        # get the folder name from the config or generate a temp folder
        folder_name = params.get_value('folder_name')
        if folder_name:
            temp_dir = os.path.join(Settings.get_root_temp_dir(), folder_name)
            FileHelper.create_dir_if_not_exist(temp_dir)
        else:
            temp_dir = Settings.get_root_temp_dir()

        configs: List[dict] = params.get_value('filenames')

        i = 0
        resource_list: ResourceList = inputs['source']
        for resource in resource_list.get_resources():
            if not isinstance(resource, FSNode):
                self.log_error_message(f"Resource {i} is not a file nor a folder")
                continue

            # retrive the node name from config or use the base name
            node_name: str = None
            if len(configs) > i and configs[i] and configs[i]['filename']:
                node_name = configs[i]['filename']
            else:
                node_name = resource.get_base_name()

            FileHelper.copy_node(resource.path, os.path.join(temp_dir, node_name))
            i += 1

        return {'folder': Folder(temp_dir)}
