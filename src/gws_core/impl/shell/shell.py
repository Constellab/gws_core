# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import subprocess
import tempfile
from abc import abstractmethod
from typing import Union

from ...config.config_types import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...core.model.sys_proc import SysProc
from ...impl.file.file_service import FileService
from ...task.task import Task
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from ..file.file import File


@task_decorator("Shell")
class Shell(Task):
    """
    Shell task.

    This class is a proxy to run user shell commands through the Python method `subprocess.run`.
    """

    input_specs = {}
    output_specs = {}
    config_specs = {}

    _out_type = "text"
    _tmp_dir = None
    _shell_mode = False
    _stdout = ""
    _stdout_count = 0
    _STDOUT_MAX_CHAR_LENGHT = 1024*10

    def build_command(self, params: ConfigParams, inputs: TaskInputs) -> list:
        """
        Builds the user command to execute.

        :return: The list of arguments used to build the final command in the Python method `subprocess.run`
        :rtype: `list`
        """

        return [""]

    def build_os_env(self) -> dict:
        """
        Creates the OS environment variables that are passed to the shell command

        :return: The OS environment variables
        :rtype: `dict`
        """

        return None

    def _format_command(self, user_cmd: list) -> Union[list, str]:
        """
        Format the user command

        :param stdout: The final command
        :param type: `list`, `str`
        """

        if self._shell_mode:
            return " && ".join(user_cmd)
        else:
            return user_cmd

    @abstractmethod
    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """
        This methods gathers the results of the shell task. It must be overloaded by subclasses.

        It must be overloaded to capture the standard output (stdout) and the
        output files generated in the current working directory (see `gws.Shell.cwd`)

        :param stdout: The standard output of the shell task
        :type stdout: `str`
        """

        pass

    def on_stdout_change(self, stdout_count: int = 0, stdout_line: str = "") -> tuple:
        """
        This methods is triggered each time the stdout of the shell subtask has changed.

        It can be overloaded to update the progress bar for example.

        :param stdout_count: The current count of stdout lines
        :type stdout_count: `int`
        :param stdout_line: The last standard output line
        :type stdout_line: `str`

        """

        self._stdout_count = stdout_count
        self._stdout += stdout_line
        if len(self._stdout) > self._STDOUT_MAX_CHAR_LENGHT:
            self._stdout = self._stdout[-self._STDOUT_MAX_CHAR_LENGHT:]

    @property
    def cwd(self) -> tempfile.TemporaryDirectory:
        """
        The temporary working directory where the shell command is executed.
        This directory is removed at the end of the task

        :return: a file-like object built with `tempfile.TemporaryDirectory`
        :rtype: `file object`
        """

        if self._tmp_dir is None:
            self._tmp_dir = tempfile.TemporaryDirectory()

        return self._tmp_dir

    @property
    def working_dir(self) -> str:
        """
        Returns the working dir of the shell task

        :return: The working dir oif the shell task
        :rtype: `srt`
        """

        return self.cwd.name

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """
        Task entrypoint
        """

        outputs: TaskOutputs
        try:
            user_cmd = self.build_command(params, inputs)
            user_env = self.build_os_env()

            if (user_env is not None) and (not isinstance(user_env, dict)):
                raise BadRequestException(
                    "Method 'build_os_env' must return a dictionnary")

            if not user_env:
                user_env = None

            if not isinstance(user_cmd, list):
                raise BadRequestException(
                    "Method 'build_command' must return a list of string. Please set 'shell_mode=True' to format your custom shell command")

            cmd = [str(c) for c in user_cmd]
            cmd = self._format_command(cmd)

            if not os.path.exists(self.working_dir):
                os.makedirs(self.working_dir)

            proc = SysProc.popen(
                cmd,
                cwd=self.working_dir,
                env=user_env,
                shell=self._shell_mode,
                stdout=subprocess.PIPE
            )

            count = 0
            for line in iter(proc.stdout.readline, b''):
                line = line.decode().strip()
                self.add_progress_message(line)
                if not proc.is_alive():
                    break

                self.on_stdout_change(stdout_count=count, stdout_line=line)
                count += 1
            outputs = self.gather_outputs(params, inputs)
            self.cwd.cleanup()
            self._tmp_dir = None

        except subprocess.CalledProcessError as err:
            self.cwd.cleanup()
            self._tmp_dir = None
            raise BadRequestException(
                f"An error occured while running the binary in shell task. Error: {err}") from err
        except Exception as err:
            self.cwd.cleanup()
            self._tmp_dir = None
            raise BadRequestException(
                f"An error occured while running shell task. Error: {err}") from err

        return outputs


class CondaShell(Shell):
    """
    CondaShell task.

    This class is a proxy to run user shell commands through the Python method `subtask.run`.
    """

    _shell_mode = True

    def _format_command(self, user_cmd: list) -> str:
        if isinstance(user_cmd, list):
            user_cmd = [str(c) for c in user_cmd]
            user_cmd = ' '.join(user_cmd)

        cmd = 'bash -c "source /opt/conda/etc/profile.d/conda.sh && conda activate base && ' + user_cmd + '"'
        return cmd
