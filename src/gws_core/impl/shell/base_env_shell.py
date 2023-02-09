# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from abc import abstractmethod
from json import dump, load
from pathlib import Path
from typing import Any, TypedDict, Union, final

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper

from .shell_proxy import ShellProxy


class VEnvCreationInfo(TypedDict):
    file_version: int
    name: str
    created_at: str
    # path of the file that was used to create the env
    origin_env_config_file_path: str


class BaseEnvShell(ShellProxy):

    env_dir_name: str = None
    env_file_path: str = None

    VENV_DIR_NAME = ".venv"
    CREATION_INFO_FILE_NAME = "__creation.json"

    def __init__(self, env_dir_name: str, env_file_path: str,
                 working_dir: str = None, message_dispatcher: MessageDispatcher = None):
        super().__init__(working_dir, message_dispatcher)
        self.env_dir_name = env_dir_name
        self.env_file_path = env_file_path

        # check env file path
        if isinstance(env_file_path, str):
            if not FileHelper.exists_on_os(env_file_path):
                raise Exception(
                    f"The environment file '{env_file_path}' does not exist")
        else:
            raise Exception("Invalid env file path")

    def run(self, cmd: Union[list, str], env: dict = None, shell_mode: bool = False) -> int:

        formatted_cmd = self.format_command(cmd)

        # compute env
        if env is None:
            env = {}
        complete_env = {**self.build_os_env(), **env}

        # install env if not installed
        self.install_env()

        return super().run(formatted_cmd, complete_env, shell_mode)

    @final
    def check_output(self, cmd: Union[list, str], env: dict = None, text: bool = True,
                     shell_mode: bool = False) -> Any:
        formatted_cmd = self.format_command(cmd)

        # compute env
        if env is None:
            env = {}
        complete_env = {**self.build_os_env(), **env}

        # install env if not installed
        self.install_env()

        return super().check_output(formatted_cmd, complete_env, text, shell_mode)

    @final
    def install_env(self) -> bool:
        """
        Install the virtual env.
        Return True if the env was installed, False if it was already installed, or an error occured.
        """

        if self.env_is_installed():
            if self._check_if_config_file_changed():
                self._message_dispatcher.notify_info_message(
                    f"The virtual environment '{self.env_dir_name}' is already installed but the config file has changed.")
                self.uninstall_env()
            else:
                # environment already installed and ok
                self._message_dispatcher.notify_info_message(
                    f"Virtual environment '{self.env_dir_name}' already installed, skipping installation.")
                return False

        self.create_env_dir()

        self._message_dispatcher.notify_info_message(
            f"Installing the virtual environment '{self.env_dir_name}' from file '{self.env_file_path}'. This might take few minutes.")

        is_install: bool = False
        try:
            is_install = self._install_env()
        except Exception as err:
            Logger.log_exception_stack_trace(err)
            raise Exception(f"Cannot install the virtual environment. Error {err}") from err

        if is_install:
            self._create_env_creation_file()
            self._message_dispatcher.notify_info_message(f"Virtual environment '{self.env_dir_name}' installed!")

        return is_install

    def _check_if_config_file_changed(self) -> bool:
        """
        Checks if the env config file has changed since the last installation.
        If the env is not installed, return False.
        """
        if not self.env_is_installed():
            return False

        # load the creation info file
        with open(self.get_config_file_path(), "r", encoding='utf-8') as f:
            current_config = f.read()

        # loads the new config
        with open(self.env_file_path, "r", encoding='utf-8') as f:
            new_config = f.read()

        # check if the env config file has changed
        return current_config != new_config

    @abstractmethod
    def _install_env(self) -> bool:
        """
        Override this method to install the environment.
        """

    def uninstall_env(self) -> bool:
        """
        Uninstall the virtual env.
        Return true if the env was uninstalled, False if it was already uninstalled or an error occured.
        """
        if not self.env_is_installed():
            return False

        self._message_dispatcher.notify_info_message(f"Uninstalling the virtual environment '{self.env_dir_name}'")
        is_uninstall: bool = False
        try:
            is_uninstall = self._uninstall_env()
        except Exception as err:
            Logger.log_exception_stack_trace(err)
            raise Exception(f"Cannot uninstall the virtual environment. Error {err}") from err

        if is_uninstall:
            self._message_dispatcher.notify_info_message(f"Virtual environment '{self.env_dir_name}' uninstalled!")

        return is_uninstall

    @abstractmethod
    def _uninstall_env(self) -> bool:
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
    def format_command(self, user_cmd: Union[list, str]) -> str:
        """
        Format the user command

        :param stdout: The final command
        :param type: `list`
        """

    @abstractmethod
    def get_config_file_path(self) -> str:
        """
        Returns the path of the config file used to create the env
        """

    @final
    def env_is_installed(self) -> bool:
        """
        Returns True if the virtual env is installed. False otherwise
        """

        return self.folder_is_env(self.get_env_dir_path())

    @final
    def _create_env_creation_file(self) -> None:
        """
        Create the READY file
        """
        env_info: VEnvCreationInfo = {
            'file_version': 1,
            'name': self.env_dir_name,
            'created_at': DateHelper.now_utc().isoformat(),
            'origin_env_config_file_path': self.env_file_path
        }

        with open(self._get_json_info_file_path(), "w", encoding="UTF-8") as outfile:
            dump(env_info, outfile)

    def _get_json_info_file_path(self) -> str:
        """
        Returns the path of the READY file.

        The info file is automatically created in the env dir after it is installed.
        and it contains information about the env creation
        """
        return os.path.join(self.get_env_dir_path(), self.CREATION_INFO_FILE_NAME)

    def _get_ready_file_path(self) -> str:
        """
        Returns the path of the READY file.

        The READY file is automatically created in the env dir after it is installed.
        Name of the file to detect if the env is installed.
        We consider the env installed if the READY file exists.
        """

        return os.path.join(self.get_env_dir_path(), "READY")

    @final
    def get_env_dir_path(self) -> str:
        """
        Returns the absolute path for the env dir base on a dir name.
        All env are in the global env dir.
        """

        env_dir = os.path.join(Settings.get_global_env_dir(), self.env_dir_name)

        return env_dir

    @final
    def create_env_dir(self) -> Path:
        """
        Create the env dir.
        """

        return FileHelper.create_dir_if_not_exist(self.get_env_dir_path())

    @classmethod
    def folder_is_env(cls, folder_path: str) -> bool:
        """return true if the folder is a valid env folder"""
        return FileHelper.exists_on_os(os.path.join(folder_path, cls.CREATION_INFO_FILE_NAME))

    @classmethod
    def get_creation_info(cls, folder_path: str) -> VEnvCreationInfo:
        """
        Returns the json info file content
        """
        if not cls.folder_is_env(folder_path):
            raise Exception("The virtual environment is not installed")

        with open(os.path.join(folder_path, cls.CREATION_INFO_FILE_NAME), encoding="UTF-8") as json_file:
            return load(json_file)
