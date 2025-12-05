import hashlib
import os
import subprocess
from abc import abstractmethod
from json import dump, load
from pathlib import Path
from typing import Any, Literal, TypeVar, final

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.model.sys_proc import SysProc
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.shell.virtual_env.venv_dto import VEnvCreationInfo

from .shell_proxy import ShellProxy, ShellProxyDTO, ShellProxyEnvVariableMode

BaseEnvShellType = TypeVar("BaseEnvShellType", bound="BaseEnvShell")


class BaseEnvShell(ShellProxy):
    env_name: str = None
    env_hash: str = None
    env_file_path: str = None

    VENV_DIR_NAME = ".venv"
    CREATION_INFO_FILE_NAME = "__creation.json"

    # overrided by subclasses. Use to define the default env file name
    CONFIG_FILE_NAME: str = None

    def __init__(
        self,
        env_file_path: Path | str,
        env_name: str = None,
        working_dir: str = None,
        message_dispatcher: MessageDispatcher = None,
    ):
        """_summary_

        :param env_name: Name of the environment. This name will be shown in the env list. If not provided, a name is generated
        :type env_name: str
        :param env_file_path: path to the env file. This file must contained dependencies for the virtual env and
                              will be used to create the env. If the env file has changed, the env will be recreated and
                              previous env will be deleted.
        :type env_file_path: str
        :param working_dir: working directory for the shell (all command will be executed from this dir).
                            If not provided, an new temp directory is created. defaults to None
        :type working_dir: str, optional
        :param message_dispatcher: if provided, the output of the command will be redirected to the dispatcher.
                                  Can be useful to log command outputs in task's logs. defaults to None
        :type message_dispatcher: MessageDispatcher, optional
        :raises Exception: _description_
        :raises Exception: _description_
        """
        super().__init__(working_dir, message_dispatcher)

        # check env file path
        if not isinstance(env_file_path, (str, Path)):
            raise Exception("Invalid env file path")
        if not FileHelper.exists_on_os(env_file_path):
            raise Exception(f"The environment file '{env_file_path}' does not exist")
        self.env_file_path = str(env_file_path)
        self.env_hash = self._generate_env_hash()

        if env_name:
            self.env_name = env_name
        else:
            self.env_name = self.env_hash

    def _generate_env_hash(self) -> str:
        """
        Generate a hash from the env file to create a unique env dir name.
        """

        try:
            with open(self.env_file_path, encoding="utf-8") as file:
                env_str = file.read()

            return self.hash_env_str(env_str)
        except Exception as err:
            raise Exception(f"Error while reading the env file. Error {err}") from err

    def run(
        self,
        cmd: list | str,
        env: dict = None,
        env_mode: ShellProxyEnvVariableMode = ShellProxyEnvVariableMode.MERGE,
        shell_mode: bool = False,
        dispatch_stdout: bool = False,
        dispatch_stderr: bool = True,
    ) -> int:
        """
        Run a command in a shell.
        The logs of the command will be dispatched to the message dispatcher during the execution.

        :param cmd: command to run
        :type cmd: Union[list, str]
        :param env: environment variables to pass to the shell, defaults to None
        :type env: dict, optional
        :param env_mode: mode to use for the environment variables, defaults to ShellProxyEnvVariableMode.MERGE
        :type env_mode: ShellProxyEnvVariableMode, optional
        :param shell_mode: if True, the command is run in a shell, defaults to False
        :type shell_mode: bool, optional
        :param dispatch_stdout: if True, the stdout of the command is dispatched to the message dispatcher.
                            ⚠️ Warning ⚠️ Do not set to True if the command generates a lot of logs,
                            because logs are stored in database, defaults to False
        :type dispatch_stdout: bool, optional
        :param dispatch_stderr: if True, the stderr of the command is dispatched to the message dispatcher.
                            ⚠️ Warning ⚠️ Do not set to True if the command generates a lot of logs,
                            because logs are stored in database, defaults to True
        :type dispatch_stderr: bool, optional
        """
        formatted_cmd = self.format_command(cmd)

        # install env if not installed
        self.install_env()

        return super().run(
            formatted_cmd, env, env_mode, shell_mode, dispatch_stdout, dispatch_stderr
        )

    def run_in_new_thread(
        self,
        cmd: list | str,
        env: dict = None,
        env_mode: ShellProxyEnvVariableMode = ShellProxyEnvVariableMode.MERGE,
        shell_mode: bool = False,
    ) -> SysProc:
        """
        Run a command in a shell without blocking the thread.
        There logs of the command are ignored.

        :param cmd: command to run
        :type cmd: Union[list, str]
        :param env: environment variables to pass to the shell, defaults to None
        :type env: dict, optional
        :param env_mode: mode to use for the environment variables, defaults to ShellProxyEnvVariableMode.MERGE
        :type env_mode: ShellProxyEnvVariableMode, optional
        :param shell_mode: if True, the command is run in a shell, defaults to False
        :type shell_mode: bool, optional
        :return: Thread running the command
        :rtype: threading.Thread
        """
        formatted_cmd = self.format_command(cmd)

        # install env if not installed
        self.install_env()

        return super().run_in_new_thread(formatted_cmd, env, env_mode, shell_mode)

    @final
    def check_output(
        self,
        cmd: list | str,
        env: dict = None,
        env_mode: ShellProxyEnvVariableMode = ShellProxyEnvVariableMode.MERGE,
        shell_mode: bool = False,
        text: bool = True,
    ) -> Any:
        """
        Run a command in a shell and return the output.
        There logs of the command are ignored.

        :param cmd: command to run
        :type cmd: Union[list, str]
        :param env: environment variables to pass to the shell, defaults to None
        :type env: dict, optional
        :param env_mode: mode to use for the environment variables, defaults to ShellProxyEnvVariableMode.MERGE
        :type env_mode: ShellProxyEnvVariableMode, optional
        :param shell_mode: if True, the command is run in a shell, defaults to False
        :type shell_mode: bool, optional
        :param text: if True, the output is returned as a string, defaults to True
        :type text: bool, optional
        :raises Exception: _description_
        :return: output of the command
        :rtype: Any
        """
        formatted_cmd = self.format_command(cmd)

        # install env if not installed
        self.install_env()

        return super().check_output(formatted_cmd, env, env_mode, shell_mode, text)

    @final
    def install_env(self) -> bool:
        """
        Install the virtual env.
        Return True if the env was installed, False if it was already installed, or an error occured.
        """

        if self.env_is_installed():
            # environment already installed and ok
            self._message_dispatcher.notify_info_message(
                f"Virtual environment '{self.env_name}' already installed, skipping installation."
            )
            return False

        self.create_env_dir()

        self._message_dispatcher.notify_info_message(
            f"Installing the virtual environment '{self.env_name}' from file '{self.env_file_path}' into folder {self.get_env_dir_path()}'. This might take few minutes."
        )

        is_install: bool = False
        try:
            is_install = self._install_env()
        except Exception as err:
            # delete the env dir if an error occured
            FileHelper.delete_dir(self.get_env_dir_path())

            Logger.log_exception_stack_trace(err)
            raise Exception(f"Cannot install the virtual environment. Error {err}") from err

        if is_install:
            self._create_env_creation_file()
            self._message_dispatcher.notify_info_message(
                f"Virtual environment '{self.env_name}' installed!"
            )

        return is_install

    def _execute_env_install_command(self, cmd: str, env: dict[str, str] = None) -> None:
        """
        Execute the command to install the virtual env, and log error if any.
        """
        res: subprocess.CompletedProcess = subprocess.run(
            cmd,
            cwd=self.get_env_dir_path(),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=True,
            check=False,
        )

        if res.returncode != 0:
            error_message = res.stderr.decode("utf-8") or res.stdout.decode("utf-8")
            self._message_dispatcher.notify_error_message(error_message)
            raise Exception(f"Cannot install the virtual environment. Error: {error_message}")

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

        self._message_dispatcher.notify_info_message(
            f"Uninstalling the virtual environment '{self.env_name}'"
        )
        is_uninstall: bool = False
        try:
            is_uninstall = self._uninstall_env()
        except Exception as err:
            Logger.log_exception_stack_trace(err)
            raise Exception(f"Cannot uninstall the virtual environment. Error {err}") from err

        if is_uninstall:
            self._message_dispatcher.notify_info_message(
                f"Virtual environment '{self.env_name}' uninstalled!"
            )

        return is_uninstall

    @abstractmethod
    def _uninstall_env(self) -> bool:
        """
        Uninstall the virtual env.
        """

    def _execute_uninstall_command(self, cmd: str, env: dict[str, str] = None) -> None:
        res = subprocess.run(
            cmd,
            cwd=self.get_env_dir_path(),
            env=env,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            shell=True,
            check=False,
        )
        if res.returncode != 0:
            try:
                if FileHelper.exists_on_os(self.get_env_dir_path()):
                    FileHelper.delete_dir(self.get_env_dir_path())

            except Exception as err:
                error_message = res.stderr.decode("utf-8") or res.stdout.decode("utf-8")
                self._message_dispatcher.notify_error_message(error_message)
                raise Exception(f"Cannot remove the virtual environment. {error_message}") from err

    @abstractmethod
    def format_command(self, user_cmd: list | str) -> list | str:
        """
        Format the user command. If the command is a list, must return a list.
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
        env_info = VEnvCreationInfo(
            file_version=2,
            name=self.env_name,
            hash=self.env_hash,
            created_at=DateHelper.now_utc().isoformat(),
            origin_env_config_file_path=self.env_file_path,
            env_type=self.get_env_type(),
        )

        with open(self._get_json_info_file_path(), "w", encoding="UTF-8") as outfile:
            dump(env_info.to_json_dict(), outfile)

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

        return os.path.join(Settings.get_global_env_dir(), self.env_hash)

    @final
    def create_env_dir(self) -> Path:
        """
        Create the env dir.
        """

        return FileHelper.create_dir_if_not_exist(self.get_env_dir_path())

    @final
    def read_env_file(self) -> str:
        """
        Read the env file and return its content.
        """

        with open(self.env_file_path, encoding="utf-8") as file:
            return file.read()

    @classmethod
    def folder_is_env(cls, folder_path: str) -> bool:
        """return true if the folder is a valid env folder"""
        return FileHelper.exists_on_os(os.path.join(folder_path, cls.CREATION_INFO_FILE_NAME))

    @classmethod
    def get_creation_info(cls, folder_path: str) -> VEnvCreationInfo:
        """
        Returns the json info file content
        """
        if not FileHelper.exists_on_os(folder_path):
            raise Exception("The virtual environment is not installed")

        with open(
            os.path.join(folder_path, cls.CREATION_INFO_FILE_NAME), encoding="UTF-8"
        ) as json_file:
            return VEnvCreationInfo.from_json(load(json_file))

    @classmethod
    def from_env_str(
        cls: type[BaseEnvShellType], env_str: str, message_dispatcher: MessageDispatcher = None
    ) -> BaseEnvShellType:
        """
        Create the virtual environment from a string containing the environment definition.

        The env dir name is generated from an hash of the env_str.
        So if the env_str is the same, the env dir name will be the same.
        """

        env_hash = cls.hash_env_str(env_str)
        temp_dir = Settings.make_temp_dir()
        env_file_path = os.path.join(temp_dir, cls.CONFIG_FILE_NAME)
        with open(env_file_path, "w", encoding="utf-8") as file_path:
            file_path.write(env_str)

        return cls(
            env_name=env_hash, env_file_path=env_file_path, message_dispatcher=message_dispatcher
        )

    @classmethod
    def hash_env_str(cls, env_str: str) -> str:
        """
        Create a hash from the env_str to generate a unique env dir name.
        """

        # remove all the white spaces and new lines
        env_to_hash = env_str.replace(" ", "").replace("\n", "")
        return hashlib.md5(env_to_hash.encode("utf-8")).hexdigest()

    @classmethod
    @abstractmethod
    def get_env_type(cls) -> Literal["conda", "mamba", "pip"]:
        """
        Returns the type of the env
        """

    def to_dto(self) -> ShellProxyDTO:
        return ShellProxyDTO(
            typing_name=self.get_typing_name(),
            env_code=self.read_env_file(),
        )
