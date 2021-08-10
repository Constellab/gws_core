# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import subprocess
import tempfile
import shutil

from gws.exception.bad_request_exception import BadRequestException
from gws.logger import Logger

from ..system import SysProc
from ..shell import Shell
from .base_env import BaseEnvShell

class PipEnvShell(BaseEnvShell):
    """
    EnvShell process.

    This class is a proxy to run user shell commands through the Python method `subprocess.run`.
    """

    _python_version = "3.8"

    # -- B --

    def _format_command(self, user_cmd) -> list:
        """
        This method builds the command to execute.

        :return: The list of arguments used to build the final command in the Python method `subprocess.run`
        :rtype: `list`
        """

        if  user_cmd[0] in ["python", "python2", "python3"]:
           del user_cmd[0]

        return [ "pipenv", "run", "python", *user_cmd ]

    def build_env(self) -> dict:
        env = os.environ.copy()
        env["PIPENV_PIPFILE"] = self.get_pipfile_path()
        env["PIPENV_VENV_IN_PROJECT"] = "enabled"
        return env

    # -- E --

    @classmethod
    def get_pipfile_path(cls) -> str:
        """
        Returns the directory of the virtual env of the process class
        """

        return os.path.join(cls.get_env_dir(), "Pipfile")

    # -- I --

    @classmethod
    def install(cls):
        """
        Install the virtual env
        """

        if cls.is_installed():
            return
        dep = list(set([
            *cls._dependencies
        ]))
        dep = " ".join(dep)
        cmd = [
            f"pipenv --python {cls._python_version}",
            "&&",
            f"pipenv install {dep}",
            "&&"
            "touch READY",
        ]

        try:
            Logger.progress("Installing the virtual environment ...")
            subprocess.check_call(
                " ".join(cmd),
                cwd=cls.get_env_dir(),
                stderr=subprocess.DEVNULL,
                shell=True
            )
            Logger.progress("Virtual environment installed!")
        except Exception as err:
            raise BadRequestException("Cannot install the virtual environment.") from err
    
    @classmethod
    def uninstall(cls):
        if not cls.is_installed():
            return
        cmd = [
            "pipenv uninstall --all",
            "&&",
            "cd ..",
            "&&",
            f"rm -rf {cls.get_env_dir()}"
        ]
        try:
            Logger.progress("Removing the virtual environment ...")
            subprocess.check_call(
                " ".join(cmd),
                cwd=cls.get_env_dir(),
                stderr=subprocess.DEVNULL,
                shell=True
            )
            Logger.progress("Virtual environment removed!")
        except Exception as err:
            try:
                if os.path.exists(cls.get_env_dir()):
                    shutil.rmtree(cls.get_env_dir())
            except:
                raise BadRequestException("Cannot remove the virtual environment.")