# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import shutil
import subprocess
from abc import abstractmethod

from ...config.config_types import ConfigValues
from ...core.exception.exceptions import BadRequestException
from ...progress_bar.progress_bar import ProgressBar
from ...task.task_decorator import task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from .base_env import BaseEnvShell


@task_decorator("PipEnvShell")
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

    # -- B --

    def _format_command(self, user_cmd) -> list:
        """
        This method builds the command to execute.

        :return: The list of arguments used to build the final command in the Python method `subprocess.run`
        :rtype: `list`
        """

        if user_cmd[0] in ["python", "python2", "python3"]:
            del user_cmd[0]
        return ["pipenv", "run", "python", *user_cmd]

    def build_os_env(self) -> dict:
        env = os.environ.copy()
        pipfile_path = os.path.join(self.get_env_dir(), "Pipfile")
        env["PIPENV_PIPFILE"] = pipfile_path
        env["PIPENV_VENV_IN_PROJECT"] = "enabled"
        return env

    # -- E --

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
        pipfile_path = os.path.join(cls.get_env_dir(), "Pipfile")
        cmd = [
            f"cp {cls.env_file_path} {pipfile_path}", "&&",
            "pipenv install", "&&",
            "touch READY"
        ]
        try:
            ProgressBar.add_message_to_current(
                "Installing the virtual environment ...")
            env = os.environ.copy()
            env["PIPENV_VENV_IN_PROJECT"] = "enabled"
            subprocess.check_call(
                " ".join(cmd),
                cwd=cls.get_env_dir(),
                stderr=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                env=env,
                shell=True
            )
            ProgressBar.add_message_to_current(
                "Virtual environment installed!")
        except Exception as err:
            raise BadRequestException(
                "Cannot install the virtual environment.") from err

    @classmethod
    def uninstall(cls):
        if not cls.is_installed():
            return
        cmd = [
            "pipenv uninstall --all", "&&",
            "cd ..", "&&",
            f"rm -rf {cls.get_env_dir()}"
        ]
        try:
            ProgressBar.add_message_to_current(
                "Removing the virtual environment ...")
            env = os.environ.copy()
            env["PIPENV_VENV_IN_PROJECT"] = "enabled"
            subprocess.check_call(
                " ".join(cmd),
                cwd=cls.get_env_dir(),
                stderr=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                env=env,
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
    def gather_outputs(self, config: ConfigValues, inputs: TaskInputs) -> TaskOutputs:
        """
        This methods gathers the results of the shell task. It must be overloaded by subclasses.

        It must be overloaded to capture the standard output (stdout) and the
        output files generated in the current working directory (see `gws.Shell.cwd`)

        :param stdout: The standard output of the shell task
        :type stdout: `str`
        """

        pass
