# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import abc
import os
import re

from ....config.config_types import ConfigParams, ConfigSpecs
from ....config.param_spec import ListParam, StrParam
from ....core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ....io.io_spec import InputSpec, OutputSpec
from ....io.io_spec_helper import InputSpecs, OutputSpecs
from ....resource.resource_set import ResourceSet
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

    > **Warning**: It is recommended to use code snippets comming from trusted sources.
    """

    input_specs: InputSpecs = {'source': InputSpec(
        (File, ResourceSet), is_optional=True, human_name="File or file set", short_description="File or file set"), }
    output_specs: OutputSpecs = {'target': OutputSpec(
        ResourceSet, sub_class=True, human_name="File set", short_description="File set"), }
    config_specs: ConfigSpecs = {
        'env': ListParam(human_name="YAML environment", short_description="YAML environment text"),
        'args':
        StrParam(
            optional=True, default_value="", human_name="Shell arguments",
            short_description="Shell arguments used to call the script. Use wildcards {input:*} to pass the input files to the script. For example: '--data1 {input:filename_1} --data2 {input:filename_2} -o out_file.txt'."),
        'code': ListParam(human_name="Code snippet", short_description="The code snippet to execute using shell command"),
        'captures':
        ListParam(
            human_name="Files to capture in outputs",
            short_description="The realitve paths of the files to capture in the outputs. For example: Enter 'out_file.txt' to capture this file in the outputs"), }

    shell_proxy: ShellProxy = None
    code_file_extension: str = None

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        code: str = params.get_value('code')
        args = params.get_value('args', "")
        env = params.get_value('env')

        # pass the input files in args
        source = inputs.get("source")
        if source is not None:
            if isinstance(source, File):
                args = re.sub("{input:.*}", source.path, args)
            else:
                for name in source.get_resources():
                    file = source.get_resource(name)
                    args = args.replace("{input:"+name+"}", file.path)

        # TODO: Delete later
        code: str = "\n".join(code)
        env: str = "\n".join(env)

        fpath: str
        captures = params.get_value('captures', None)
        for fpath in captures:
            if len(captures) != len(set(captures)):
                raise BadRequestException("The outputs files list contains duplicates")
            if fpath.startswith("/"):
                raise BadRequestException(
                    f"The outputs file path '{fpath}' is not allowed. Only relative paths are allowed.")

        self.shell_proxy = self._create_shell_proxy(env)

        # create code file
        code_file_path = os.path.join(self.shell_proxy.working_dir, f"code{self.code_file_extension}")
        with open(code_file_path, 'w', encoding='utf-8') as fp:
            fp.write(code)

        # validate user inputs, params, code
        cmd = self._format_command(code_file_path, args)
        try:
            self.shell_proxy.run(cmd, shell_mode=True)
        except Exception as err:
            raise BadRequestException(f"An error occured during the execution of the live code. Error: {err}") from err

        # gather outputs files
        target = ResourceSet()
        for filepath in captures:
            full_path = os.path.join(self.shell_proxy.working_dir, filepath)
            file = File(path=full_path)
            file.name = filepath
            target.add_resource(file)

        return {'target': target}

    async def run_after_task(self) -> None:
        """
        This can be overwritten to perform action after the task run. This method is called after the
        resource save. Temp object can be safely deleted here, the resources will still exist
        """

        self.shell_proxy.clean_working_dir()

    @ abc.abstractmethod
    def _format_command(self, code_file_path: str, args: str) -> list:
        pass

    @ abc.abstractmethod
    def _create_shell_proxy(self, env: str) -> ShellProxy:
        pass
