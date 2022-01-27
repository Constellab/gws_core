# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import shlex
import shutil
import subprocess
from abc import abstractmethod

from ...config.config_types import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...progress_bar.progress_bar import ProgressBar, ProgressBarMessageType
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from .base_env import BaseEnvShell
from ...task.task import Task


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

    @ classmethod
    def install(cls, current_task:Task=None):
        """
        Install the virtual env
        """
        if (current_task is not None) and not isinstance(current_task, Task):
            raise BadRequestException(f"The current task must be an instance of Task")

        if cls.is_installed():
            return
        if isinstance(cls.env_file_path, str):
            if not os.path.exists(cls.env_file_path):
                raise BadRequestException(
                    f"The dependency file '{cls.env_file_path}' does not exist")
        else:
            raise BadRequestException("Invalid env file path")
        cmd = [
            'bash -c "source /opt/conda/etc/profile.d/conda.sh"', "&&",
            f"conda env create -f {cls.env_file_path} --force --prefix ./.venv", "&&",
            "touch READY",
        ]

        res: subprocess.CompletedProcess
        try:
            if current_task:
                current_task.log_info_message("Installing the virtual environment ...")
            res = subprocess.run(
                " ".join(cmd),
                cwd=cls.get_env_dir(),
                stderr=subprocess.PIPE,
                shell=True
            )
        except Exception as err:
            raise BadRequestException("Cannot install the virtual environment.") from err

        if res.returncode != 0:
            raise BadRequestException(f"Cannot install the virtual environment. Error: {res.stderr}")

        if current_task:
            current_task.log_success_message("Virtual environment installed!")

    # -- U --

    @ classmethod
    def uninstall(cls, current_task:Task=None):
        if (current_task is not None) and not isinstance(current_task, Task):
            raise BadRequestException(f"The current task must be an instance of Task")

        if not cls.is_installed():
            return
        cmd = [
            'bash -c "source /opt/conda/etc/profile.d/conda.sh"', "&&",
            "conda remove -y --prefix .venv --all", "&&",
            "cd ..", "&&",
            f"rm -rf {cls.get_env_dir()}"
        ]

        res: subprocess.CompletedProcess
        try:
            if current_task:
                current_task.log_info_message("Removing the virtual environment ...")
            res = subprocess.run(
                " ".join(cmd),
                cwd=cls.get_env_dir(),
                stderr=subprocess.PIPE,
                shell=True
            )
        except Exception as err:
            try:
                if os.path.exists(cls.get_env_dir()):
                    shutil.rmtree(cls.get_env_dir())
            except Exception as err:
                raise BadRequestException("Cannot remove the virtual environment.") from err

        if res.returncode != 0:
            raise BadRequestException(f"Cannot remove the virtual environment. Error: {res.stderr}")

        if current_task:
            current_task.log_info_message("Virtual environment removed!")

    @ abstractmethod
    def gather_outputs(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """
        This methods gathers the results of the shell task. It must be overloaded by subclasses.

        It must be overloaded to capture the standard output (stdout) and the
        output files generated in the current working directory (see `gws.Shell.cwd`)

        :param stdout: The standard output of the shell task
        :type stdout: `str`
        """

        pass
