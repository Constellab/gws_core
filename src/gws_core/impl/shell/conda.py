# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from abc import abstractmethod

from gws_core.impl.shell.conda_helper import CondaHelper

from ...config.config_types import ConfigParams
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from .base_env import BaseEnvShell


@task_decorator("CondaEnvShell", hide=True)
class CondaEnvShell(BaseEnvShell):
    """
    CondaEnvShell task.

    This class allows to run python scripts in conda virtual environments. It rely on the awesome
    Conda containerization system to efficiently automate the management of your venvs.
    See also https://conda.io/.

    :property env_file_path: The dependencies to install. Could be a list of modules or the path of a dependency file.
    :type env_file_path: `list`,`str`

    For conda, a typical yml environment file content is:
        ```
        name: my_env_name
        channels:
          - javascript
          - conda-forge
        dependencies:
          - r-base=3.1.2
          - r-tidyverse
          - python=3.6
          - bokeh=0.9.2
          - numpy=1.9.*
          - nodejs=0.10.*
          - flask
          - pip:
            - Flask-Testing
        ```
    """

    env_file_path: str = None
    _shell_mode = True

    # -- F --

    def _format_command(self, user_cmd: list) -> str:
        if isinstance(user_cmd, list):
            user_cmd = [str(c) for c in user_cmd]
            user_cmd = " ".join(user_cmd)
        venv_dir = os.path.join(self.get_env_dir(), "./.venv")
        cmd = f'bash -c "source /opt/conda/etc/profile.d/conda.sh && conda activate {venv_dir} && {user_cmd}"'
        return cmd

    # -- G --

    # -- I --

    def install(self):
        """
        Install the virtual env
        """

        if self.is_installed():
            return

        self.log_info_message("Installing the virtual environment, this might take few minutes.")

        CondaHelper.install_env(self.env_file_path, self.get_env_dir())

        self.log_info_message("Virtual environment installed!")

    # -- U --

    def uninstall(self):
        if self.is_installed():
            return

        self.log_info_message("Removing the virtual environment ...")

        CondaHelper.uninstall_env(self.get_env_dir())

        self.log_info_message("Virtual environment removed!")

    @abstractmethod
    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """
        This methods gathers the results of the shell task. It must be overloaded by subclasses.

        It must be overloaded to capture the standard output (stdout) and the
        output files generated in the current working directory (see `gws.Shell.cwd`)

        :param stdout: The standard output of the shell task
        :type stdout: `str`
        """
