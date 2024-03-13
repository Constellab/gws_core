

import json
import os
import shutil
from abc import abstractmethod
from typing import List

from gws_core.config.param.param_spec import ListParam, ParamSpec
from gws_core.impl.file.folder import Folder
from gws_core.impl.file.fs_node import FSNode
from gws_core.io.dynamic_io import DynamicInputs, DynamicOutputs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.resource.resource_set.resource_list import ResourceList

from ....config.config_params import ConfigParams
from ....config.config_types import ConfigParamsDict, ConfigSpecs
from ....core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ....io.io_specs import InputSpecs, OutputSpecs
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

    # source_paths variable contains the list of input files and folders.
    # Each file or folder in the target_path folder are exported as output resources.

    > **Warning**: It is recommended to use code snippets comming from trusted sources.
    """

    input_specs: InputSpecs = DynamicInputs(
        additionnal_port_spec=InputSpec(FSNode, human_name="File or folder", is_optional=True))
    output_specs: OutputSpecs = DynamicOutputs(
        additionnal_port_spec=OutputSpec(FSNode, human_name="File or folder", sub_class=True))

    # override this in subclasses
    config_specs: ConfigSpecs = {}
    SNIPPET_FILE_EXTENSION: str = None

    shell_proxy: ShellProxy = None

    target_temp_folder: str = None

    SOURCE_PATHS_VAR_NAME = 'source_paths'
    TARGET_PATHS_VAR_NAME = 'target_paths'
    TARGET_PATHS_FILENAME = '__target_paths__.json'

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        code: str = params.get_value('code')
        env = params.get_value('env')

        # build the source path
        source_paths = self.get_source_path(inputs.get("source"))

        self.shell_proxy = self._create_shell_proxy(env)

        # create the executable code file
        code_file_path = self.generate_code_file(code, params.get_value('params'),
                                                 source_paths)

        # validate user inputs, params, code
        cmd = self._format_command(code_file_path)
        result: int = None
        result = self.shell_proxy.run(cmd, shell_mode=True)

        if result != 0:
            raise BadRequestException(
                "An error occured during the execution of the live code. Please view the logs for more details.")

        target = self.get_target_resources()
        return {'target': target}

    def generate_code_file(self, code: str, params: List[str], source_paths: List[str]) -> str:
        # create the executable code file
        if self.SNIPPET_FILE_EXTENSION is None:
            raise BadRequestException("No SNIPPET_FILE_EXTENSION defined")

        # format code to add inputs
        formatted_code = self._format_code(code, params, source_paths)
        code_file_path = os.path.join(
            self.shell_proxy.working_dir, f"code.{self.SNIPPET_FILE_EXTENSION}")

        # write the file
        with open(code_file_path, 'w', encoding='utf-8') as file_path:
            file_path.write(formatted_code)

        return code_file_path

    def get_source_path(self, source: ResourceList) -> List[str]:
        if source is None or len(source) == 0:
            return []

        nodes: List[FSNode] = []
        skipped_resources: List[str] = []

        for resource in source:
            if resource is None:
                continue
            if isinstance(resource, FSNode):
                nodes.append(resource)
            else:
                skipped_resources.append(resource.name)

        if len(skipped_resources) > 0:
            raise Exception(
                f"The resources {skipped_resources} are not a file or folder. To include them you must convert theses resources to file or folder (using exporter).")

        return [x.path for x in nodes]

    def get_target_resources(self) -> ResourceList:
        # read the target paths json file
        target_path_file = os.path.join(self.shell_proxy.working_dir,
                                        self.TARGET_PATHS_FILENAME)

        if not os.path.exists(target_path_file):
            raise BadRequestException(
                "the target file path was not generated. Did you write paths in the targets_paths variable ?")

        target_paths: List[str] = None
        try:
            with open(target_path_file, 'r', encoding='utf-8') as file_path:
                target_paths = json.load(file_path)
        except Exception as err:
            raise BadRequestException(f"Cannot parse the target paths file : {err}") from err

        # check if the target paths are valid
        if not isinstance(target_paths, list):
            raise BadRequestException("The target_paths variable does not contain a list of paths.")

        if len(target_path_file) == 0:
            raise BadRequestException(
                "The code snippet did not generate any output file or folder. Did you forget to write path result in target_paths variable ?")

        resource_list = ResourceList()
        for path in target_paths:
            if not isinstance(path, str):
                raise Exception(f"The path {path} in target_path variable is not a string. It will be ignored.")

            # check if path is absolute
            if not os.path.isabs(path):
                path = os.path.join(self.shell_proxy.working_dir, path)

            if not os.path.exists(path):
                raise Exception(f"The path {path} in target_path variable does not exist. It will be ignored.")

            if os.path.isdir(path):
                resource_list.append(Folder(path))
            else:
                resource_list.append(File(path))

        return resource_list

    @abstractmethod
    def _format_command(self, code_file_path: str) -> list:
        pass

    @abstractmethod
    def _create_shell_proxy(self, env: str) -> ShellProxy:
        pass

    def _format_code(self, code: str, params: List[str], source_paths: List[str]) -> str:
        """
        Format the code to add parameters and input/output paths
        """

        # format the param to string and include the last carry return
        # only if there are some param, this is useful to limit the line number difference
        # when error occured
        str_params = '\n' + ('\n'.join(params) + '\n') if len(params) > 0 else ''

        init_code = self._get_init_code(self.SOURCE_PATHS_VAR_NAME, source_paths,
                                        self.TARGET_PATHS_VAR_NAME)
        write_target_code = self._get_write_target_paths_code(self.TARGET_PATHS_VAR_NAME,
                                                              self.TARGET_PATHS_FILENAME)
        return f"""{init_code}{str_params}
{code}
# Generated section to write the target paths file
{write_target_code}
"""

    def _get_init_code(self, source_paths_var_name: str,
                       source_paths: List[str], target_paths_var_name: str) -> str:
        """
        Generate the code to initialize the source and target paths variables
        """

        return f"""{source_paths_var_name} = {source_paths}
{target_paths_var_name} = []"""

    def _get_write_target_paths_code(self, target_paths_var_name: str,
                                     target_paths_filename: str) -> str:
        """
        Generate the code to write the target paths to a file
        """
        return f"""
import json
with open('{target_paths_filename}', 'w') as f:
    json.dump({target_paths_var_name}, f)
"""

    def run_after_task(self) -> None:
        """
        This can be overwritten to perform action after the task run. This method is called after the
        resource save. Temp object can be safely deleted here, the resources will still exist
        """

        self.shell_proxy.clean_working_dir()

        if self.target_temp_folder:
            shutil.rmtree(self.target_temp_folder, ignore_errors=True)

    @classmethod
    def get_list_param_config(cls) -> ParamSpec:
        return ListParam(
            optional=True, default_value=[],
            human_name="Parameter definitions",
            short_description="Please give one parameter definition per line (https://constellab.community/bricks/gws_core/latest/doc/developer-guide/live-task/getting-started#parameters)")

    @classmethod
    def build_config_params_dict(cls, code: str, params: List[str], env: str) -> ConfigParamsDict:
        return {'code': code, "params": params, "env": env}
