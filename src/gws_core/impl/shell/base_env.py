# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from abc import abstractmethod

from ...config.config_types import ConfigParams
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from .base_env_helper import BaseEnvHelper
from .shell import Shell


@task_decorator("BaseEnvShell", hide=True)
class BaseEnvShell(Shell):
    """
    EnvShell task.

    This class is a proxy to run user shell commands in virtual environments

    :property unique_env_name: The unique name of the virtual environment.
        If `None`, a unique name is automtically defined for the Task.
        The share virtual environments across diffrent task,
        it is recommended to set (freeze) the ```unique_env_name``` in a base class and let other
        compatible tasks inherit this base class.
    :type unique_env_name: `str`
    """

    unique_env_name = None
    _shell_mode = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not os.path.exists(self.get_env_dir()):
            os.makedirs(self.get_env_dir())

    @classmethod
    def get_env_dir(cls) -> str:
        """
        Returns the directory of the virtual env of the task class
        """

        if not cls.unique_env_name:
            cls.unique_env_name = cls.full_classname()

        return BaseEnvHelper.get_env_full_dir(cls.unique_env_name, True)

    @classmethod
    def is_installed(cls) -> bool:
        """
        Returns True if the virtual env is installed. False otherwise
        """

        return BaseEnvHelper.is_installed(cls.get_env_dir())

    # -- T --

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """
        Task entrypoint
        """

        if not self.is_installed():
            self.install()
        return await super().run(params, inputs)

    def install(self) -> None:
        """
        Installs the virtual env
        """

    def uninstall(self) -> None:
        """
        Uninstalls the virtual env
        """

    @abstractmethod
    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """
        This methods gathers the results of the shell task. It must be overloaded by subclasses.

        It must be overloaded to capture the standard output (stdout) and the
        output files generated in the current working directory (see `gws.Shell.cwd`)

        :param stdout: The standard output of the shell task
        :type stdout: `str`
        """
