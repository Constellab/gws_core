
import os
from typing import Union

from typing_extensions import Literal

from gws_core.impl.file.file_helper import FileHelper

from .base_env_shell import BaseEnvShell


class PipShellProxy(BaseEnvShell):

    CONFIG_FILE_NAME = "Pipfile"
    LOCK_FILE_NAME = "Pipfile.lock"

    def _install_env(self) -> bool:
        """
        Install an environment from a conda environment file.
        Return true if the env was installed, False if it was already installed.
        """

        pipfile_path = self.get_pip_file_path()
        cmd = [
            f"cp {self.env_file_path} {pipfile_path}", "&&",
            "pipenv install"
        ]

        env = os.environ.copy()
        env["PIPENV_VENV_IN_PROJECT"] = "enabled"

        self._message_dispatcher.notify_info_message(
            f"Installing pipenv env with command: {' '.join(cmd)}.")

        self._execute_env_install_command(" ".join(cmd), env)

        return True

    def _uninstall_env(self) -> bool:
        """ Uninstall the environment.
        Return true if the env was uninstalled, False if it was already uninstalled.
        """

        cmd = [
            "pipenv uninstall --all", "&&",
            "cd ..", "&&",
            f"rm -rf {self.get_env_dir_path()}"
        ]

        env = os.environ.copy()
        env["PIPENV_VENV_IN_PROJECT"] = "enabled"

        self._message_dispatcher.notify_info_message(
            f"Uninstalling pipenv env with command: {' '.join(cmd)}.")

        self._execute_uninstall_command(" ".join(cmd), env)

        return True

    def format_command(self, user_cmd: Union[list, str]) -> Union[list, str]:
        """
        This method builds the command to execute.

        :return: The list of arguments used to build the final command in the Python method `subprocess.run`
        :rtype: `list`
        """

        if isinstance(user_cmd, list):
            cmd = [str(c) for c in user_cmd]
            return ["pipenv", "run", *cmd]
        else:
            return f"pipenv run {user_cmd}"

    def build_os_env(self) -> dict:
        env = os.environ.copy()
        pipfile_path = self.get_pip_file_path()
        env["PIPENV_PIPFILE"] = pipfile_path
        env["PIPENV_VENV_IN_PROJECT"] = "enabled"
        return env

    def get_pip_file_path(self) -> str:
        return os.path.join(self.get_env_dir_path(), "Pipfile")

    def get_config_file_path(self) -> str:
        return os.path.join(self.get_env_dir_path(), self.CONFIG_FILE_NAME)

    @classmethod
    def folder_is_env(cls, folder_path: str) -> bool:
        """return true if the folder is a valid env folder"""

        pipfile_path = os.path.join(folder_path, cls.CONFIG_FILE_NAME)
        pipfile_lock_path = os.path.join(folder_path, cls.LOCK_FILE_NAME)
        sub_venv_path = os.path.join(folder_path, cls.VENV_DIR_NAME)

        return super().folder_is_env(folder_path) and \
            FileHelper.exists_on_os(pipfile_path) and \
            FileHelper.exists_on_os(pipfile_lock_path) and \
            FileHelper.exists_on_os(sub_venv_path)

    @classmethod
    def get_env_type(cls) -> Literal['conda', 'mamba', 'pip']:
        return 'pip'
