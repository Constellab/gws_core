# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import subprocess
from typing import Type, List, Any
from .base_env import BaseEnvShell
from ...core.exception.exceptions import BadRequestException


class ShellEnvProxy:
    """
    Shell task proxy.

    This class is a proxy to Shell task. It allows using any shell task to run commands
    """

    _shell_task_type: Type[BaseEnvShell]

    def __init__( self, shell_task_type: Type[BaseEnvShell] ):
        if not issubclass(shell_task_type, BaseEnvShell):
            BadRequestException("The shell_task_type must be a subclass of BaseEnvShell")
        self._shell_task_type = shell_task_type

    def check_output(self, cmd: List[str], text: bool=True ) -> Any:
        shell_task = self._shell_task_type()
        shell_task.install()
        env_cmd = shell_task._format_command( cmd )
        env_dir = shell_task.build_os_env()

        text = subprocess.check_output(
            env_cmd,
            text=text,
            env=env_dir,
            shell=self._shell_task_type._shell_mode
        )

        return text