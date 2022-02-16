# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import subprocess
import time
from typing import Any, List, Type

from ...core.exception.exceptions import BadRequestException
from ...task.task_helper import TaskHelper
from .base_env import BaseEnvShell
from .shell import Shell


class ShellProxy(TaskHelper):
    """
    Shell task proxy.

    This class is a proxy to Shell task. It allows using any shell task to run commands
    """

    _shell_task_type: Type[Shell]

    def __init__(self, shell_task_type: Type[Shell]):
        super().__init__()
        if not issubclass(shell_task_type, Shell):
            BadRequestException("The shell_task_type must be a subclass of Shell")
        self._shell_task_type = shell_task_type

    def check_output(self, cmd: List[str], text: bool = True, cwd: str = None, shell_mode: bool = False) -> Any:
        shell_task = self._shell_task_type()
        env_cmd = shell_task._format_command(cmd)
        env_dir = shell_task.build_os_env()
        if isinstance(shell_task, BaseEnvShell):
            self._shell_task_type.install()
            shell_mode = shell_task._shell_mode
        if not cwd:
            cwd = shell_task.working_dir

        try:
            output = subprocess.check_output(
                env_cmd,
                cwd=cwd,
                text=text,
                env=env_dir,
                shell=shell_mode
            )
            return output
        except Exception as err:
            shell_task._clean_working_dir()
            raise BadRequestException(f"The shell process has failed. Error {err}.")

    def run(self, cmd: List[str], text: bool = True, cwd: str = None, shell_mode: bool = False) -> Any:
        shell_task = self._shell_task_type()
        env_cmd = shell_task._format_command(cmd)
        env_dir = shell_task.build_os_env()
        if isinstance(shell_task, BaseEnvShell):
            self._shell_task_type.install()
            shell_mode = shell_task._shell_mode
        if not cwd:
            cwd = shell_task.working_dir

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=env_dir,
                shell=shell_mode,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            tic_a = time.perf_counter()
            stdout: list = []
            for line in iter(proc.stdout.readline, b''):
                stdout.append(line.decode().strip())
                tic_b = time.perf_counter()
                if tic_b - tic_a >= 0.1:      # save outputs every 0.1 sec in taskbar
                    self.notify_info_message("\n".join(stdout))
                    tic_a = time.perf_counter()
                    stdout = []
            if stdout:
                self.notify_info_message("\n".join(stdout))
        except Exception as err:
            shell_task._clean_working_dir()
            raise BadRequestException(f"The shell process has failed. Error {err}.")
