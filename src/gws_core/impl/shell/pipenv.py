# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from abc import abstractmethod

from gws_core.impl.shell.pipenv_helper import PipEnvHelper

from ...config.config_types import ConfigParams
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from .base_env import BaseEnvShell


@task_decorator("PipEnvShell", hide=True)
class PipEnvShell(BaseEnvShell):
    """
    PipEnvShell task.

    This class allows to run python scripts in pipenv virtual environments. It rely on the awesome
    Pipenv module to efficiently automate the management of your venvs.
    See also https://pipenv.pypa.io/.

    :property env_file_path: The dependencies to install. Could be a list of modules or the path of a dependency file.
    :type env_file_path: `list`,`str`

    * A typical environment Pipefile is:
        ```
        [[source]]
        url = 'https://pypi.python.org/simple'
        verify_ssl = true
        name = 'pypi'

        [requires]
        python_version = '3.8'

        [packages]
        requests = { extras = ['socks'] }
        records = '>0.5.0'
        django = { git = 'https://github.com/django/django.git', ref = '1.11.4', editable = true }
        ```
    """

    env_file_path: str
    _shell_mode = True

    # -- B --

    def _format_command(self, user_cmd) -> list:
        """
        This method builds the command to execute.

        :return: The list of arguments used to build the final command in the Python method `subprocess.run`
        :rtype: `list`
        """

        if isinstance(user_cmd, list):
            user_cmd = [str(c) for c in user_cmd]
        if user_cmd[0] in ["python", "python2", "python3"]:
            del user_cmd[0]
        user_cmd = ["pipenv", "run", "python", *user_cmd]
        cmd = " ".join(user_cmd)
        return cmd

    def build_os_env(self) -> dict:
        env = os.environ.copy()
        pipfile_path = os.path.join(self.get_env_dir(), "Pipfile")
        env["PIPENV_PIPFILE"] = pipfile_path
        env["PIPENV_VENV_IN_PROJECT"] = "enabled"
        return env

    # -- E --

    # -- I --

    def install(self):
        """
        Install the virtual env
        """
        if self.is_installed():
            return

        self.log_info_message("Installing the virtual environment, this might take few minutes.")

        PipEnvHelper.install_env(self.env_file_path, self.get_env_dir())

        self.log_info_message("Virtual environment installed!")

    def uninstall(self):
        if not self.is_installed():
            return

        self.log_info_message("Uninstalling the virtual environment ...")

        PipEnvHelper.uninstall_env(self.get_env_dir())

        self.log_info_message("Virtual environment uninstalled!")

    @abstractmethod
    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """
        This methods gathers the results of the shell task. It must be overloaded by subclasses.

        It must be overloaded to capture the standard output (stdout) and the
        output files generated in the current working directory (see `gws.Shell.cwd`)

        :param stdout: The standard output of the shell task
        :type stdout: `str`
        """

    async def run_after_task(self) -> None:
        await super().run_after_task()
        self.uninstall()
