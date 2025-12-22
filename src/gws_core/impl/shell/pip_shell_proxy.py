import os
from typing import Literal

from gws_core.impl.file.file_helper import FileHelper
from gws_core.model.typing_register_decorator import typing_registrator

from .base_env_shell import BaseEnvShell


@typing_registrator(unique_name="PipShellProxy", object_type="MODEL", hide=True)
class PipShellProxy(BaseEnvShell):
    """Shell proxy for managing Pipenv virtual environments.

    This class manages Python virtual environments using Pipenv, which uses Pipfile
    and Pipfile.lock for dependency management. It provides:
    - Automatic Pipenv environment creation from Pipfile
    - Command execution within the Pipenv environment
    - Environment cleanup and management

    The virtual environment is created in the project directory (.venv subdirectory)
    using the PIPENV_VENV_IN_PROJECT setting.
    """
    CONFIG_FILE_NAME = "Pipfile"
    LOCK_FILE_NAME = "Pipfile.lock"

    def _install_env(self) -> bool:
        """Install a Pipenv environment from a Pipfile.

        Copies the Pipfile to the environment directory and runs `pipenv install`
        to create the virtual environment and install dependencies.

        :return: True if the environment was installed, False if it was already installed
        :rtype: bool
        """

        pipfile_path = self.get_pip_file_path()
        cmd = [f"cp {self.env_file_path} {pipfile_path}", "&&", "pipenv install"]

        env = os.environ.copy()
        env["PIPENV_VENV_IN_PROJECT"] = "enabled"

        self._message_dispatcher.notify_info_message(
            f"Installing pipenv env with command: {' '.join(cmd)}."
        )

        self._execute_env_install_command(" ".join(cmd), env)

        return True

    def _uninstall_env(self) -> bool:
        """Uninstall the Pipenv environment.

        Removes all packages from the environment and deletes the environment directory.

        :return: True if the environment was uninstalled, False if it was already uninstalled
        :rtype: bool
        """

        cmd = ["pipenv uninstall --all", "&&", "cd ..", "&&", f"rm -rf {self.get_env_dir_path()}"]

        env = os.environ.copy()
        env["PIPENV_VENV_IN_PROJECT"] = "enabled"

        self._message_dispatcher.notify_info_message(
            f"Uninstalling pipenv env with command: {' '.join(cmd)}."
        )

        self._execute_uninstall_command(" ".join(cmd), env)

        return True

    def format_command(self, user_cmd: list | str) -> list | str:
        """Format the user command to run within the Pipenv environment.

        Prepends `pipenv run` to the user command to ensure it executes within
        the virtual environment context.

        :param user_cmd: The command to format
        :type user_cmd: list | str
        :return: Formatted command with `pipenv run` prefix
        :rtype: list | str
        """

        if isinstance(user_cmd, list):
            cmd = [str(c) for c in user_cmd]
            return ["pipenv", "run", *cmd]
        else:
            return f"pipenv run {user_cmd}"

    def get_default_env_variables(self) -> dict:
        """Get default environment variables for Pipenv execution.

        Sets PIPENV_PIPFILE to point to the Pipfile location and enables
        PIPENV_VENV_IN_PROJECT to create the virtual environment in the project directory.

        :return: Dictionary of environment variables
        :rtype: dict
        """
        return {
            "PIPENV_PIPFILE": self.get_pip_file_path(),
            "PIPENV_VENV_IN_PROJECT": "enabled",
        }

    def get_pip_file_path(self) -> str:
        """Get the path to the Pipfile.

        :return: Absolute path to the Pipfile
        :rtype: str
        """
        return os.path.join(self.get_env_dir_path(), "Pipfile")

    def get_config_file_path(self) -> str:
        """Get the path to the Pipfile configuration file.

        :return: Absolute path to the Pipfile
        :rtype: str
        """
        return os.path.join(self.get_env_dir_path(), self.CONFIG_FILE_NAME)

    @classmethod
    def folder_is_env(cls, folder_path: str) -> bool:
        """Check if a folder is a valid Pipenv environment folder.

        Validates that the folder contains a Pipfile, Pipfile.lock, and .venv directory.

        :param folder_path: Path to check
        :type folder_path: str
        :return: True if the folder is a valid Pipenv environment folder
        :rtype: bool
        """

        pipfile_path = os.path.join(folder_path, cls.CONFIG_FILE_NAME)
        pipfile_lock_path = os.path.join(folder_path, cls.LOCK_FILE_NAME)
        sub_venv_path = os.path.join(folder_path, cls.VENV_DIR_NAME)

        return (
            super().folder_is_env(folder_path)
            and FileHelper.exists_on_os(pipfile_path)
            and FileHelper.exists_on_os(pipfile_lock_path)
            and FileHelper.exists_on_os(sub_venv_path)
        )

    @classmethod
    def get_env_type(cls) -> Literal["conda", "mamba", "pip"]:
        """Get the environment type identifier.

        :return: The string "pip"
        :rtype: Literal["conda", "mamba", "pip"]
        """
        return "pip"
