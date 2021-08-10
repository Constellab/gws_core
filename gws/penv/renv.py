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

class REnvShell(BaseEnvShell):
    """
    REnvShell process.

    This class allows to run R scripts in renv virtual environments.
    See also https://rstudio.github.io/renv/
    """

    _python_version = "3.8"

    # -- B --

    def _format_command(self, user_cmd) -> list:
        """
        This method builds the command to execute.

        :return: The list of arguments used to build the final command in the Python method `subprocess.run`
        :rtype: `list`
        """

        if  user_cmd[0] in ["R", "Rscript", "/usr/bin/R", "/usr/bin/Rscript"]:
           del user_cmd[0]

        return [ "Rscript", "--vanilla", *user_cmd ]

    # -- E --

    def get_install_file_path():
        
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
        __cdir__ = os.path.abspath(os.path.realpath(__file__))
        cmd = [
            f"Rscript --vanilla {}",
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
                stdout=subprocess.DEVNULL,
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
                stdout=subprocess.DEVNULL,
                shell=True
            )
            Logger.progress("Virtual environment removed!")
        except Exception as err:
            try:
                if os.path.exists(cls.get_env_dir()):
                    shutil.rmtree(cls.get_env_dir())
            except:
                raise BadRequestException("Cannot remove the virtual environment.")