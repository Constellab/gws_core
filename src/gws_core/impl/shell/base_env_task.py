# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractmethod
from typing import Union

from ...config.config_types import ConfigParams
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from .base_env import BaseEnv
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

    base_env: BaseEnv = None

    _shell_mode = False

    @classmethod
    def get_env_dir_name(cls) -> str:
        """
        Returns the directory of the virtual env of the task class
        """

        if not cls.unique_env_name:
            cls.unique_env_name = cls.full_classname()

        return cls.unique_env_name

    def is_installed(self) -> bool:
        """
        Returns True if the virtual env is installed. False otherwise
        """

        return self.base_env.is_installed()

    # -- T --

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """
        Task entrypoint
        """

        if not self.is_installed():
            self.install()
        return await super().run(params, inputs)

    def install(self):
        """
        Install the virtual env
        """
        if self.is_installed():
            self.log_info_message(
                f"Virtual environment '{self.base_env.env_dir_name}' already installed, skipping installation.")
            return

        self.log_info_message(
            f"Installing the virtual environment '{self.base_env.env_dir_name}' from file '{self.base_env.env_file_path}',  this might take few minutes.")

        self.base_env.install()

        self.log_info_message(f"Virtual environment '{self.base_env.env_dir_name}' installed!")

    def uninstall(self):
        if not self.is_installed():
            return

        self.log_info_message("Uninstalling the virtual environment ...")

        self.base_env.uninstall()

        self.log_info_message("Virtual environment uninstalled!")

    def build_os_env(self) -> dict:
        """
        Creates the OS environment variables that are passed to the shell command

        :return: The OS environment variables
        :rtype: `dict`
        """

        return self.base_env.build_os_env()

    def _format_command(self, user_cmd: list) -> Union[list, str]:
        """
        Format the user command

        :param stdout: The final command
        :param type: `list`, `str`
        """

        return self.base_env.format_command(user_cmd)

    @abstractmethod
    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """
        This methods gathers the results of the shell task. It must be overloaded by subclasses.

        It must be overloaded to capture the standard output (stdout) and the
        output files generated in the current working directory (see `gws.Shell.cwd`)

        :param stdout: The standard output of the shell task
        :type stdout: `str`
        """
