# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import shutil
import subprocess
from abc import abstractmethod

from ...config.config_params import ConfigParams
from ...core.exception.exceptions import BadRequestException
from ...process.process_decorator import process_decorator
from ...process.process_io import ProcessInputs, ProcessOutputs
from ...progress_bar.progress_bar import ProgressBar
from .base_env import BaseEnvShell


@process_decorator("CondaEnvShell")
class CondaEnvShell(BaseEnvShell):
    """
    CondaEnvShell process.

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
            user_cmd = ' '.join(user_cmd)
        venv_dir = os.path.join(self.get_env_dir(), "./.venv")
        cmd = f'bash -c "source /opt/conda/etc/profile.d/conda.sh && conda activate {venv_dir} && {user_cmd}"'
        return cmd

    # -- G --

    # -- I --

    @classmethod
    def install(cls):
        """
        Install the virtual env
        """

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
        try:
            ProgressBar.add_message_to_current(
                "Installing the virtual environment ...")
            subprocess.check_call(
                " ".join(cmd),
                cwd=cls.get_env_dir(),
                stderr=subprocess.DEVNULL,
                shell=True
            )
            ProgressBar.add_message_to_current(
                "Virtual environment installed!")
        except Exception as err:
            raise BadRequestException(
                "Cannot install the virtual environment.") from err

    # -- U --

    @classmethod
    def uninstall(cls):
        if not cls.is_installed():
            return
        cmd = [
            "conda remove -y --prefix .venv --all", "&&",
            "cd ..", "&&",
            f"rm -rf {cls.get_env_dir()}"
        ]
        try:
            ProgressBar.add_message_to_current(
                "Removing the virtual environment ...")
            subprocess.check_call(
                " ".join(cmd),
                cwd=cls.get_env_dir(),
                stderr=subprocess.DEVNULL,
                shell=True
            )
            ProgressBar.add_message_to_current("Virtual environment removed!")
        except:
            try:
                if os.path.exists(cls.get_env_dir()):
                    shutil.rmtree(cls.get_env_dir())
            except:
                raise BadRequestException(
                    "Cannot remove the virtual environment.")

    @abstractmethod
    def gather_outputs(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        """
        This methods gathers the results of the shell process. It must be overloaded by subclasses.

        It must be overloaded to capture the standard output (stdout) and the
        output files generated in the current working directory (see `gws.Shell.cwd`)

        :param stdout: The standard output of the shell process
        :type stdout: `str`
        """

        pass
