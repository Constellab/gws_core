# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from abc import abstractmethod

from ...config.config_params import ConfigParams
from ...process.process_decorator import ProcessDecorator
from ...process.process_io import ProcessInputs, ProcessOutputs
from .shell import Shell


@ProcessDecorator("BaseEnvShell")
class BaseEnvShell(Shell):
    """
    EnvShell process.

    This class is a proxy to run user shell commands in virtual environments

    :property unique_env_name: The unique name of the virtual environment.
        If `None`, a unique name is automtically defined for the Process.
        The share virtual environments across diffrent process,
        it is recommended to set (freeze) the ```unique_env_name``` in a base class and let other
        compatible processes inherit this base class.
    :type unique_env_name: `str`
    """

    unique_env_name = None
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

        if not cls.unique_env_name:
            cls.unique_env_name = cls.full_classname()
        return os.path.join(cls._GLOBAL_ENV_DIR, cls.unique_env_name)

    # -- I --

    @classmethod
    def _get_ready_file_path(cls) -> str:
        """
        Returns the path of the READY file.

        The READY file is automatically created in the env dir after it is installed.
        """

        return os.path.join(cls.get_env_dir(), "READY")

    @classmethod
    def is_installed(cls) -> bool:
        """
        Returns True if the virtual env is installed. False otherwise
        """

        return os.path.exists(cls._get_ready_file_path())

    @classmethod
    def install(cls) -> None:
        """
        Installs the virtual env
        """

        pass

    # -- T --

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        """
        Task entrypoint
        """

        if not self.is_installed():
            self.install()
        return await super().task(config=config, inputs=inputs)

    # -- U --

    @classmethod
    def uninstall(cls) -> None:
        """
        Uninstalls the virtual env
        """

        pass

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