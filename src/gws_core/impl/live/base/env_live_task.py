# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import shutil
from abc import abstractmethod
from typing import List, Optional

from gws_core.config.param.param_spec import ListParam, ParamSpec
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.folder import Folder
from gws_core.impl.file.fs_node import FSNode
from gws_core.resource.resource import Resource

from ....config.config_types import ConfigParams, ConfigSpecs
from ....core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ....io.io_spec import InputSpec, OutputSpec
from ....io.io_spec_helper import InputSpecs, OutputSpecs
from ....resource.resource_set.resource_set import ResourceSet
from ....task.task import Task
from ....task.task_decorator import task_decorator
from ....task.task_io import TaskInputs, TaskOutputs
from ...file.file import File
from ...shell.shell_proxy import ShellProxy


@task_decorator("EnvLiveTask", human_name="Env live task",
                short_description="Live task to run code snippets in a shell environment. The inputs files are passed to the snippet through the arguments.",
                hide=True)
class EnvLiveTask(Task):
    """
    This task executes code snippets on the fly in shell environments.

    # If a File is passed as input, we should create a temporary folder and copy the file in it. Pass the file path to the snippet.
    # If a Folder is passed as input, we should create a temporary folder and copy the folder in it. Pass the folder path to the snippet.
    # If a ResourceSet is passed as input, we should create a temporary folder and copy the files in it. Pass the temps folder path to the snippet.

    # Path a result folder to the snippet. The snippet should write the outputs files in this folder.
    # If the folder contains only 1 file or folder, we should return this file or folder as output.
    # If the folder contains more than 1 file or folder, we should return the ResourceSet as output.


    > **Warning**: It is recommended to use code snippets comming from trusted sources.
    """

    input_specs: InputSpecs = {'source': InputSpec(
        (File, Folder, ResourceSet), is_optional=True, human_name="File or file set", short_description="File or file set"), }
    output_specs: OutputSpecs = {'target': OutputSpec(
        (File, Folder, ResourceSet), sub_class=True, human_name="File set", short_description="File set")}

    # override this in subclasses
    config_specs: ConfigSpecs = {}
    SNIPPET_FILE_EXTENSION: str = None

    shell_proxy: ShellProxy = None

    source_temp_folder: str = None
    target_temp_folder: str = None

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        code: str = params.get_value('code')
        env = params.get_value('env')

        # build the target path
        self.target_temp_folder = Settings.make_temp_dir()

        # build the source path
        self.source_temp_folder = self.get_source_path(inputs.get("source"))

        self.shell_proxy = self._create_shell_proxy(env)

        # create the executable code file
        code_file_path = self.generate_code_file(code, params.get_value('params'),
                                                 self.target_temp_folder,
                                                 self.source_temp_folder)

        # validate user inputs, params, code
        cmd = self._format_command(code_file_path)
        result: int = None
        try:
            result = self.shell_proxy.run(cmd, shell_mode=True)
        except Exception as err:
            raise BadRequestException(
                f"An error occured during the execution of the live code. Please view the logs for more details. Error: {err}") from err

        if result != 0:
            raise BadRequestException(
                "An error occured during the execution of the live code. Please view the logs for more details.")

        target = self.get_target_resources(self.target_temp_folder)
        return {'target': target}

    def generate_code_file(self, code: str, params: List[str], target_path: str, source_path: str) -> str:
        # create the executable code file
        if self.SNIPPET_FILE_EXTENSION is None:
            raise BadRequestException("No SNIPPET_FILE_EXTENSION defined")

        # format code to add inputs
        formatted_code = self._format_code(
            code, params, target_path, source_path)
        code_file_path = os.path.join(
            self.shell_proxy.working_dir, f"code.{self.SNIPPET_FILE_EXTENSION}")

        # write the file
        with open(code_file_path, 'w', encoding='utf-8') as file_path:
            file_path.write(formatted_code)

        return code_file_path

    def get_source_path(self, source: Resource) -> str:
        if source is None:
            return ''

        if isinstance(source, FSNode):
            return source.path

        # for ResourceSet, add all the file and folder in a temp folder
        elif isinstance(source, ResourceSet):
            source_folder = Settings.make_temp_dir()

            count = 0
            for sub_resources in source.get_resources().values():
                if isinstance(sub_resources, FSNode):
                    temp_file_path = os.path.join(
                        source_folder, sub_resources.get_default_name())
                    shutil.copyfile(sub_resources.path, temp_file_path)
                    count += 1

            if count == 0:
                raise BadRequestException(
                    "ResourceSet input does not contain any file or folder.")

            return source_folder
        else:
            raise BadRequestException(
                f"Source type {source._human_name} is not supported. Only File, Folder and ResourceSet containing Files or Folders are supported.")

    def get_target_resources(self, target_path: str) -> Resource:
        # count the files and folders directly in the result folder
        count = len(os.listdir(target_path))

        if count == 0:
            raise BadRequestException(
                "The code snippet did not generate any output file or folder. Did you forget to write the output files in the target folder?")

        if count == 1:
            # if there is only 1 file or folder, return it
            for name in os.listdir(target_path):
                path = os.path.join(target_path, name)
                if os.path.isdir(path):
                    return Folder(path)
                else:
                    return File(path)

        # if there is more than 1 file or folder, return a ResourceSet
        resource_set = ResourceSet()
        for name in os.listdir(target_path):
            path = os.path.join(target_path, name)
            if os.path.isdir(path):
                resource_set.add_resource(Folder(path), name)
            else:
                resource_set.add_resource(File(path), name)

        return resource_set

    @abstractmethod
    def _format_command(self, code_file_path: str) -> list:
        pass

    @abstractmethod
    def _create_shell_proxy(self, env: str) -> ShellProxy:
        pass

    def _format_code(self, code: str, params: List[str], target_path: str, source_path: Optional[str]) -> str:
        """
        Format the code to add parameters and input/output paths
        """

        # format the param to string and include the last carry return
        # only if there are some param, this is useful to limit the line number difference
        # when error occured
        str_params = '\n' + ('\n'.join(params) + '\n') if len(params) > 0 else ''
        return f"""target_folder = "{target_path}"
source_path = "{source_path}"{str_params}
{code}
"""

    def run_after_task(self) -> None:
        """
        This can be overwritten to perform action after the task run. This method is called after the
        resource save. Temp object can be safely deleted here, the resources will still exist
        """

        self.shell_proxy.clean_working_dir()

        if self.source_temp_folder:
            shutil.rmtree(self.source_temp_folder, ignore_errors=True)

        if self.target_temp_folder:
            shutil.rmtree(self.target_temp_folder, ignore_errors=True)

    @classmethod
    def get_list_param_config(cls) -> ParamSpec:
        return ListParam(
            optional=True, default_value=[],
            human_name="Parameter definitions",
            short_description="Please give one parameter definition per line (https://constellab.community/tech-doc/doc/developer-guide/live-task/getting-started#parameters)")
