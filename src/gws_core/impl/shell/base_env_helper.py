# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os

from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper


class BaseEnvHelper():

    @classmethod
    def is_installed(cls, env_dir: str) -> bool:
        """
        Returns True if the virtual env is installed. False otherwise
        """

        return FileHelper.exists_on_os(cls._get_ready_file_path(env_dir))

    @classmethod
    def _get_ready_file_path(cls, env_dir: str) -> str:
        """
        Returns the path of the READY file.

        The READY file is automatically created in the env dir after it is installed.
        """

        return os.path.join(env_dir, "READY")

    @classmethod
    def get_env_full_dir(cls, dir_name: str, create_dir_if_not_exist: bool = False) -> str:
        """
        Returns the absolute path for the env dir base on a dir name.
        All env are in the global env dir.
        """

        env_dir = os.path.join(Settings.get_global_env_dir(), dir_name)

        if create_dir_if_not_exist:
            FileHelper.create_dir_if_not_exist(env_dir)
        return env_dir
