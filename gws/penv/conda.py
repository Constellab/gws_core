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

class CondaEnvShell(BaseEnvShell):
    """
    CondaShell process.

    This class is a proxy to run user shell commands through the Python method `subprocess.run`.
    """

    _shell_mode = True
    _python_version = "3.8"

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
        dep = list(set([
            *cls._dependencies
        ]))
        dep = " ".join(dep)

        cmd = [
            'bash -c "source /opt/conda/etc/profile.d/conda.sh"',
            "&&",
            f"conda create -y --prefix ./.venv python={cls._python_version} {dep}",
            "&&",
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
            raise BadRequestException("Cannot install the virtual environment.")
    
    # -- U --

    @classmethod
    def uninstall(cls):
        if not cls.is_installed():
            return
        
        cmd = [
            "conda remove -y --prefix .venv --all",
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
