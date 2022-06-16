# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from abc import abstractmethod

from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper


class BaseEnv():

    env_dir_name: str = None
    env_file_path: str = None

    def __init__(self, env_dir_name: str, env_file_path: str):
        self.env_dir_name = env_dir_name
        self.env_file_path = env_file_path

        # check env file path
        if isinstance(env_file_path, str):
            if not FileHelper.exists_on_os(env_file_path):
                raise Exception(
                    f"The environment file '{env_file_path}' does not exist")
        else:
            raise Exception("Invalid env file path")

    @abstractmethod
    def install(self) -> bool:
        """
        Install the virtual env.
        """

    @abstractmethod
    def uninstall(self) -> bool:
        """
        Uninstall the virtual env.
        """

    def build_os_env(self) -> dict:
        """
        Creates the OS environment variables that are passed to the shell command

        :return: The OS environment variables
        :rtype: `dict`
        """

        return {}

    @abstractmethod
    def format_command(self, user_cmd: list) -> str:
        """
        Format the user command

        :param stdout: The final command
        :param type: `list`
        """

    def is_installed(self) -> bool:
        """
        Returns True if the virtual env is installed. False otherwise
        """

        return FileHelper.exists_on_os(self._get_ready_file_path())

    def _get_ready_file_path(self) -> str:
        """
        Returns the path of the READY file.

        The READY file is automatically created in the env dir after it is installed.
        """

        return os.path.join(self.get_env_dir_path(), "READY")

    def get_env_dir_path(self) -> str:
        """
        Returns the absolute path for the env dir base on a dir name.
        All env are in the global env dir.
        """

        env_dir = os.path.join(Settings.get_global_env_dir(), self.env_dir_name)

        return env_dir

    def create_env_dir(self) -> bool:
        """
        Create the env dir.
        """

        return FileHelper.create_dir_if_not_exist(self.get_env_dir_path())
