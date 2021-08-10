# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import subprocess
import tempfile

from gws.exception.bad_request_exception import BadRequestException
from gws.logger import Logger

from ..system import SysProc
from ..shell import Shell

class BaseEnvShell(Shell):
    """
    EnvShell process.

    This class is a proxy to run user shell commands in virtual environments
    """

    config_specs = {}
    _dependencies = []
    _shell_mode = False
    _GLOBAL_ENV_DIR = "/.local/share/gws/venv/"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not os.path.exists(self.get_env_dir()):
            os.makedirs(self.get_env_dir())

    @classmethod
    def get_env_dir(cls) -> str:
        """
        Returns the directory of the virtual env of the process class
        """

        return os.path.join(cls._GLOBAL_ENV_DIR, cls.full_classname())

    # -- I --

    @classmethod
    def _get_ready_file_path(cls) -> str:
        """
        Returns the path of the READY file.

        The READY file is automatically created in the env dir after it is installed.
        """

        return os.path.join(cls.get_env_dir(), "READY")

    @classmethod
    def is_installed(cls):
        """
        Returns True if the virtual env is installed. False otherwise
        """

        return os.path.exists(cls._get_ready_file_path())

    @classmethod
    def install(cls):
        """
        Installs the virtual env
        """

        pass
    
    # -- T --

    async def task(self):
        """
        Task entrypoint
        """

        if not self.is_installed():
            self.install()
        return await super().task()

    # -- U --

    @classmethod
    def uninstall(cls):
        """
        Uninstalls the virtual env
        """

        pass