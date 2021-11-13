# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import subprocess
from typing import Any, List, Type

from ...core.exception.exceptions import BadRequestException
from .base_env import BaseEnvShell
from .shell import Shell


class ShellProxy:
    """
    Shell task proxy.

    This class is a proxy to Shell task. It allows using any shell task to run commands
    """

    _shell_task_type: Type[Shell]

    def __init__(self, shell_task_type: Type[Shell]):
        if not issubclass(shell_task_type, Shell):
            BadRequestException("The shell_task_type must be a subclass of Shell")
        self._shell_task_type = shell_task_type

    def check_output(self, cmd: List[str], text: bool = True) -> Any:
        shell_task = self._shell_task_type()
        if isinstance(shell_task, BaseEnvShell):
            return self._env_shell_check_output(cmd, text)
        else:
            return self._base_shell_check_output(cmd, text)

    def _base_shell_check_output(self, cmd: List[str], text: bool = True) -> Any:
        shell_task = self._shell_task_type()
        env_cmd = shell_task._format_command(cmd)
        text = subprocess.check_output(
            env_cmd,
            text=text,
            shell=shell_task._shell_mode
        )
        return text

    def _env_shell_check_output(self, cmd: List[str], text: bool = True) -> Any:
        shell_task = self._shell_task_type()
        shell_task.install()
        env_cmd = shell_task._format_command(cmd)
        env_dir = shell_task.build_os_env()
        text = subprocess.check_output(
            env_cmd,
            text=text,
            env=env_dir,
            shell=shell_task._shell_mode
        )
        return text
