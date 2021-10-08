# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import shutil
import subprocess
import tempfile
import time
from abc import abstractmethod
from typing import Union

from ...config.config_types import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...core.model.sys_proc import SysProc
from ...core.utils.settings import Settings
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

    _out_type: str = "text"
    _tmp_dir: str = None
    _shell_mode: bool = False
    _stdout: str = ""
    _stdout_count: int = 0
    _STDOUT_MAX_CHAR_LENGHT: int = 1024*10

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

        return {}

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

    def _on_stdout_change(self, stdout_count: int = 0, stdout_line: str = "") -> tuple:
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
    def working_dir(self) -> str:
        """
        Returns the working dir of the shell task

        :return: The working dir oif the shell task
        :rtype: `srt`
        """

        if self._tmp_dir is None:
            settings = Settings.retrieve()
            self._tmp_dir = settings.make_temp_dir()

        return self._tmp_dir

    def _clean_working_dir(self):
        """
        Clean the working dir
        """

        if self._tmp_dir is not None:
            shutil.rmtree(self._tmp_dir, ignore_errors=True)
        self._tmp_dir = None

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
            tic_a = time.perf_counter()
            lines = []
            line: str
            with open(os.path.join(self.working_dir, "task.log"), "w", encoding="utf-8") as fp:
                for line in iter(proc.stdout.readline, b''):
                    count += 1
                    line = line.decode().strip()
                    tic_b = time.perf_counter()
                    lines.append(line)
                    if tic_b - tic_a >= 1:      # save outputs every N sec in taskbar
                        self.add_progress_message(f"STDOUT {count}: " + line)
                        self._on_stdout_change(stdout_count=count, stdout_line=line)
                        fp.writelines(lines)
                        lines = []
                        tic_a = time.perf_counter()
                    if not proc.is_alive():
                        break

                if lines:
                    self.add_progress_message(f"STDOUT {count}: " + line)
                    self._on_stdout_change(stdout_count=count, stdout_line=line)
                    fp.writelines(lines)

            outputs = self.gather_outputs(params, inputs)
        except subprocess.CalledProcessError as err:
            self._clean_working_dir()
            raise BadRequestException(
                f"An error occured while running the binary in shell task. Error: {err}") from err
        except Exception as err:
            self._clean_working_dir()
            raise BadRequestException(
                f"An error occured while running shell task. Error: {err}") from err

        return outputs

    async def run_after_task(self) -> None:
        """
        This can be overwritten to perform action after the task run. This method is called after the
        resource save. Temp object can be safely deleted here, the resources will still exist
        """

        self._clean_working_dir()

