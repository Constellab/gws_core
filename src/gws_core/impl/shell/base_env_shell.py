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
    """Base class for shell proxies that manage virtual environments.

    This abstract class extends ShellProxy to provide functionality for creating,
    managing, and executing commands within isolated virtual environments. It handles:
    - Virtual environment installation and uninstallation
    - Environment file hashing for version tracking
    - Command formatting for environment activation
    - Environment metadata management

    Subclasses must implement environment-specific methods for different package managers
    (conda, mamba, pip).

    Example: Running a Python script in a virtual environment
    ----------------------------------------------------------

    ⚠️ IMPORTANT: Scripts or folders must start with '_' (underscore) to be ignored during lab start ⚠️

    Example structure:
        bricks/
            my_brick/
                _scripts/              # ← Folder starts with '_' to be ignored
                    env.yml
                    _my_script.py      # ← Script starts with '_' to be ignored

    Usage example:
    ```python
    from gws_core import MambaShellProxy

    shell = MambaShellProxy(
        env_file_path="/path/to/_scripts/env.yml",
        env_name="my_script_env",  # Optional: custom name    )

    # Run your Python script
    # The virtual environment will be automatically installed if not already present
    exit_code = shell.run("python _my_script.py")
    ```

    Note: Files and folders starting with '_' are ignored by the lab system during startup,
    preventing them from being loaded as bricks or modules. This is essential for utility
    scripts, test scripts, or any code that should not be part of the main application.
    """

    env_name: str
    env_hash: str
    env_file_path: str

    VENV_DIR_NAME = ".venv"
    CREATION_INFO_FILE_NAME = "__creation.json"

    # overrided by subclasses. Use to define the default env file name
    CONFIG_FILE_NAME: str

    def __init__(
        self,
        env_file_path: Path | str,
        env_name: str | None = None,
        working_dir: str | None = None,
        message_dispatcher: MessageDispatcher | None = None,
    ):
        """Initialize a BaseEnvShell instance.

        :param env_file_path: Path to the environment file. This file must contain dependencies for the virtual env and
                              will be used to create the env. If the env file has changed, the env will be recreated and
                              the previous env will be deleted
        :type env_file_path: Path | str
        :param env_name: Name of the environment. This name will be shown in the env list. If not provided, a name is generated
                         from the environment file hash, defaults to None
        :type env_name: str, optional
        :param working_dir: Working directory for the shell (all commands will be executed from this dir).
                            If not provided, a new temp directory is created, defaults to None
        :type working_dir: str, optional
        :param message_dispatcher: If provided, the output of the command will be redirected to the dispatcher.
                                  Can be useful to log command outputs in task's logs, defaults to None
        :type message_dispatcher: MessageDispatcher, optional
        :raises Exception: If env_file_path is invalid or the file does not exist
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
        """Generate a hash from the env file to create a unique env directory name.

        The hash is based on the content of the environment file, ensuring that
        identical environment configurations share the same hash.

        :return: MD5 hash of the environment file content
        :rtype: str
        :raises Exception: If there is an error reading the env file
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
        env: dict | None = None,
        env_mode: ShellProxyEnvVariableMode = ShellProxyEnvVariableMode.MERGE,
        shell_mode: bool | None = None,
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
        :param shell_mode: if True, the command is run in a shell. If False, run without shell.
                          If None (default), automatically detect from cmd type (string -> True, list -> False)
        :type shell_mode: bool | None, optional
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
        env: dict | None = None,
        env_mode: ShellProxyEnvVariableMode = ShellProxyEnvVariableMode.MERGE,
        shell_mode: bool | None = None,
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
        :param shell_mode: if True, the command is run in a shell. If False, run without shell.
                          If None (default), automatically detect from cmd type (string -> True, list -> False)
        :type shell_mode: bool | None, optional
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
        env: dict | None = None,
        env_mode: ShellProxyEnvVariableMode = ShellProxyEnvVariableMode.MERGE,
        shell_mode: bool | None = None,
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
        :param shell_mode: if True, the command is run in a shell. If False, run without shell.
                          If None (default), automatically detect from cmd type (string -> True, list -> False)
        :type shell_mode: bool | None, optional
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

    def _execute_env_install_command(self, cmd: str, env: dict[str, str] | None = None) -> None:
        """Execute the command to install the virtual environment.

        Runs the installation command and logs any errors that occur.

        :param cmd: Shell command to execute for installation
        :type cmd: str
        :param env: Environment variables to pass to the command, defaults to None
        :type env: dict[str, str], optional
        :raises Exception: If the installation command fails
        """
        res: subprocess.CompletedProcess = subprocess.run(
            cmd,
            cwd=self.get_env_dir_path(),
            env=env,
            capture_output=True,
            shell=True,
            check=False,
        )

        if res.returncode != 0:
            error_message = res.stderr.decode("utf-8") or res.stdout.decode("utf-8")
            self._message_dispatcher.notify_error_message(error_message)
            raise Exception(f"Cannot install the virtual environment. Error: {error_message}")

    @abstractmethod
    def _install_env(self) -> bool:
        """Install the virtual environment.

        Subclasses must implement this method to provide environment-specific
        installation logic.

        :return: True if the environment was installed, False otherwise
        :rtype: bool
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
        """Uninstall the virtual environment.

        Subclasses must implement this method to provide environment-specific
        uninstallation logic.

        :return: True if the environment was uninstalled, False otherwise
        :rtype: bool
        """

    def _execute_uninstall_command(self, cmd: str, env: dict[str, str] | None = None) -> None:
        """Execute the command to uninstall the virtual environment.

        Runs the uninstallation command and attempts to delete the environment directory
        if the command fails.

        :param cmd: Shell command to execute for uninstallation
        :type cmd: str
        :param env: Environment variables to pass to the command, defaults to None
        :type env: dict[str, str], optional
        :raises Exception: If the uninstallation command fails and directory cleanup fails
        """
        res = subprocess.run(
            cmd,
            cwd=self.get_env_dir_path(),
            env=env,
            capture_output=True,
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
        """Format the user command for execution within the virtual environment.

        Subclasses must implement this to wrap commands with environment activation logic.
        If the command is a list, must return a list. If it's a string, must return a string.

        :param user_cmd: The command to format
        :type user_cmd: list | str
        :return: Formatted command ready for execution
        :rtype: list | str
        """

    @abstractmethod
    def get_config_file_path(self) -> str:
        """Get the path of the configuration file used to create the environment.

        :return: Absolute path to the config file
        :rtype: str
        """

    @final
    def env_is_installed(self) -> bool:
        """Check if the virtual environment is installed.

        :return: True if the virtual env is installed, False otherwise
        :rtype: bool
        """

        return self.folder_is_env(self.get_env_dir_path())

    @final
    def _create_env_creation_file(self) -> None:
        """Create the environment creation metadata file.

        Stores information about the environment including name, hash, creation time,
        and source configuration file path.
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
        """Get the path of the environment metadata JSON file.

        The info file is automatically created in the env directory after it is installed
        and contains information about the env creation.

        :return: Absolute path to the creation info file
        :rtype: str
        """
        return os.path.join(self.get_env_dir_path(), self.CREATION_INFO_FILE_NAME)

    def _get_ready_file_path(self) -> str:
        """Get the path of the READY marker file.

        The READY file is automatically created in the env directory after it is installed.
        This file is used to detect if the environment is fully installed.

        :return: Absolute path to the READY file
        :rtype: str
        """

        return os.path.join(self.get_env_dir_path(), "READY")

    @final
    def get_env_dir_path(self) -> str:
        """Get the absolute path for the environment directory.

        All environments are stored in the global env directory, with subdirectories
        named by their environment hash.

        :return: Absolute path to this environment's directory
        :rtype: str
        """

        return os.path.join(Settings.get_global_env_dir(), self.env_hash)

    @final
    def create_env_dir(self) -> Path:
        """Create the environment directory if it doesn't exist.

        :return: Path object for the created directory
        :rtype: Path
        """

        return FileHelper.create_dir_if_not_exist(self.get_env_dir_path())

    @final
    def read_env_file(self) -> str:
        """Read the environment configuration file and return its content.

        :return: Content of the environment file
        :rtype: str
        """

        with open(self.env_file_path, encoding="utf-8") as file:
            return file.read()

    @classmethod
    def folder_is_env(cls, folder_path: str) -> bool:
        """Check if a folder is a valid environment folder.

        :param folder_path: Path to check
        :type folder_path: str
        :return: True if the folder is a valid environment folder
        :rtype: bool
        """
        return FileHelper.exists_on_os(os.path.join(folder_path, cls.CREATION_INFO_FILE_NAME))

    @classmethod
    def get_creation_info(cls, folder_path: str) -> VEnvCreationInfo:
        """Get the environment creation information from the metadata file.

        :param folder_path: Path to the environment folder
        :type folder_path: str
        :return: Creation information for the environment
        :rtype: VEnvCreationInfo
        :raises Exception: If the virtual environment is not installed
        """
        if not FileHelper.exists_on_os(folder_path):
            raise Exception("The virtual environment is not installed")

        with open(
            os.path.join(folder_path, cls.CREATION_INFO_FILE_NAME), encoding="UTF-8"
        ) as json_file:
            return VEnvCreationInfo.from_json(load(json_file))

    @classmethod
    def from_env_str(
        cls: type[BaseEnvShellType],
        env_str: str,
        message_dispatcher: MessageDispatcher | None = None,
    ) -> BaseEnvShellType:
        """Create a virtual environment from a string containing the environment definition.

        The environment directory name is generated from a hash of the env_str,
        so identical environment strings will share the same environment directory.

        :param env_str: String containing the environment definition
        :type env_str: str
        :param message_dispatcher: Optional message dispatcher for logging, defaults to None
        :type message_dispatcher: MessageDispatcher, optional
        :return: Instance of the environment shell
        :rtype: BaseEnvShellType
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
        """Create an MD5 hash from the environment string.

        Removes whitespace and newlines before hashing to ensure consistent hashes
        for equivalent environment definitions.

        :param env_str: Environment definition string
        :type env_str: str
        :return: MD5 hash of the normalized environment string
        :rtype: str
        """

        # remove all the white spaces and new lines
        env_to_hash = env_str.replace(" ", "").replace("\n", "")
        return hashlib.md5(env_to_hash.encode("utf-8")).hexdigest()

    @classmethod
    @abstractmethod
    def get_env_type(cls) -> Literal["conda", "mamba", "pip"]:
        """Get the type of environment manager used.

        :return: Environment type identifier
        :rtype: Literal["conda", "mamba", "pip"]
        """

    def to_dto(self) -> ShellProxyDTO:
        return ShellProxyDTO(
            typing_name=self.get_typing_name(),
            env_code=self.read_env_file(),
        )
