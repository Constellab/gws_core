import json
import os
from typing import Literal

from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.shell.virtual_env.venv_dto import VEnvCreationInfo
from gws_core.model.typing_register_decorator import typing_registrator

from .base_env_shell import BaseEnvShell
from .shell_proxy import ShellProxy


@typing_registrator(unique_name="CondaShellProxy", object_type="MODEL", hide=True)
class CondaShellProxy(BaseEnvShell):
    """Shell proxy for managing Conda virtual environments.

    This class manages Python virtual environments using Conda, which uses environment.yml
    files for dependency specification. It provides:
    - Automatic Conda environment creation from environment.yml
    - Command execution within the Conda environment using `conda activate`
    - Environment cleanup and management

    The `conda_command` attribute can be overridden by subclasses (e.g., MambaShellProxy)
    to use alternative package managers like Mamba for faster installation.
    """

    CONFIG_FILE_NAME = "environment.yml"

    # can be overridden by the child class to use mamba instead of conda
    # the mamba command is only used for install and uninstall the env
    conda_command = "conda"

    def _install_env(self) -> bool:
        """Install a Conda environment from an environment.yml file.

        Creates the environment using `conda env create` with the prefix set to
        the .venv subdirectory within the environment directory.

        :return: True if the environment was installed, False if it was already installed
        :rtype: bool
        """

        # --prefix define the path where the env will be created relative to where the
        # command is executed. Command is executed in the env dir, so the path is relative to that.
        cmd = [
            self._build_str_conda_command(
                self.conda_command,
                f"env create -f {self.env_file_path} --yes --prefix ./{self.VENV_DIR_NAME}",
            )
        ]

        self._message_dispatcher.notify_info_message(
            f"Installing {self.conda_command} env with command: {' '.join(cmd)}."
        )

        self._execute_env_install_command(" ".join(cmd))

        # copy the file the was used to create the env into the env dir
        env_file_path = os.path.join(self.get_env_dir_path(), self.CONFIG_FILE_NAME)
        FileHelper.copy_file(self.env_file_path, env_file_path)

        return True

    def _uninstall_env(self) -> bool:
        """Uninstall the Conda environment.

        Removes the Conda environment and deletes the environment directory.

        :return: True if the environment was uninstalled, False if it was already uninstalled
        :rtype: bool
        """

        cmd = [
            self._build_str_conda_command(
                self.conda_command,
                f"remove -y --prefix {self.VENV_DIR_NAME} --all && cd .. && rm -rf {self.get_env_dir_path()}",
            )
        ]

        self._message_dispatcher.notify_info_message(
            f"Uninstalling {self.conda_command} env with command: {' '.join(cmd)}."
        )

        self._execute_uninstall_command(" ".join(cmd))

        return True

    def format_command(self, user_cmd: list | str) -> list | str:
        """Format the user command to run within the Conda environment.

        Prepends `conda activate` to the user command to ensure it executes within
        the virtual environment context. Always uses `conda` (not mamba) for activation.

        :param user_cmd: The command to format
        :type user_cmd: list | str
        :return: Formatted command wrapped in bash with conda activation
        :rtype: list | str
        """
        is_list = isinstance(user_cmd, list)

        str_cmd: str
        str_cmd = " ".join([str(c) for c in user_cmd]) if is_list else str(user_cmd)

        str_cmd = f"activate {self.get_venv_dir_path()} && {str_cmd}"

        # the run command must use conda, not mamba
        # use conda activate and not run, otherwise the logs are retrieve only after the command is finished (not in real time)
        if is_list:
            return self._build_list_conda_command(CondaShellProxy.conda_command, str_cmd)
        else:
            return self._build_str_conda_command(CondaShellProxy.conda_command, str_cmd)

    def get_default_env_variables(self) -> dict:
        """Get default environment variables for Conda execution.

        Sets PYTHONUNBUFFERED to force unbuffered Python output for real-time logging
        when used with conda activate.

        :return: Dictionary of environment variables
        :rtype: dict
        """

        # PYTHONUNBUFFERED is used to force the python output to be unbuffered so the log are in real time
        # (this needs to be with conda activate to be log in real time)
        return {"PYTHONUNBUFFERED": "1"}

    def get_config_file_path(self) -> str:
        """Get the path to the environment.yml configuration file.

        :return: Absolute path to the environment.yml file
        :rtype: str
        """
        return os.path.join(self.get_env_dir_path(), self.CONFIG_FILE_NAME)

    def get_venv_dir_path(self) -> str:
        """Get the path to the .venv subdirectory containing the Conda environment.

        :return: Absolute path to the .venv directory
        :rtype: str
        """
        return os.path.join(self.get_env_dir_path(), self.VENV_DIR_NAME)

    def _build_str_conda_command(self, conda_cmd: str, cmd: str) -> str:
        """Build a conda command as a string for shell execution.

        :param conda_cmd: The conda command (e.g., "conda" or "mamba")
        :type conda_cmd: str
        :param cmd: The command arguments
        :type cmd: str
        :return: Formatted command string wrapped in bash
        :rtype: str
        """
        return f'bash -c "{self._build_sub_conda_command(conda_cmd, cmd)}"'

    def _build_list_conda_command(self, conda_cmd: str, cmd: str) -> list[str]:
        """Build a conda command as a list for subprocess execution.

        :param conda_cmd: The conda command (e.g., "conda" or "mamba")
        :type conda_cmd: str
        :param cmd: The command arguments
        :type cmd: str
        :return: Formatted command as a list
        :rtype: list[str]
        """
        return ["bash", "-c", self._build_sub_conda_command(conda_cmd, cmd)]

    def _build_sub_conda_command(self, conda_cmd: str, cmd: str) -> str:
        """Build the inner conda command with environment sourcing.

        Sources the conda shell script and executes the provided command.

        :param conda_cmd: The conda command (e.g., "conda" or "mamba")
        :type conda_cmd: str
        :param cmd: The command arguments
        :type cmd: str
        :return: Complete command string with conda sourcing
        :rtype: str
        """
        return f"source /opt/conda/etc/profile.d/{CondaShellProxy.conda_command}.sh && {conda_cmd} {cmd}"

    @classmethod
    def folder_is_env(cls, folder_path: str) -> bool:
        """Check if a folder is a valid Conda/Mamba environment folder.

        Validates that the folder contains an environment.yml, .venv directory,
        and has the correct environment type (conda or mamba) in its metadata.

        :param folder_path: Path to check
        :type folder_path: str
        :return: True if the folder is a valid Conda/Mamba environment folder
        :rtype: bool
        """

        pipfile_path = os.path.join(folder_path, cls.CONFIG_FILE_NAME)
        sub_venv_path = os.path.join(folder_path, cls.VENV_DIR_NAME)

        if (
            not super().folder_is_env(folder_path)
            or not FileHelper.exists_on_os(pipfile_path)
            or not FileHelper.exists_on_os(sub_venv_path)
        ):
            return False

        try:
            env_creation_info: VEnvCreationInfo = cls.get_creation_info(folder_path)

            return env_creation_info.env_type in ["conda", "mamba"]
        except:
            return False

    def _list_packages(self) -> dict[str, str]:
        """List all installed packages with their versions in the Conda environment.

        Uses `conda list` to retrieve all packages installed in the virtual environment.

        :return: Dictionary mapping package names to their versions
        :rtype: dict[str, str]
        """
        # Build the conda list command to get packages in JSON format
        cmd = self._build_str_conda_command(
            CondaShellProxy.conda_command, f"list --prefix {self.get_venv_dir_path()} --json"
        )

        try:
            # Call ShellProxy's check_output directly, bypassing format_command
            output = ShellProxy.check_output(self, cmd, shell_mode=True, text=True)
            packages_list = json.loads(output)

            # Convert list of dicts to dict of name: version
            packages_dict = {}
            for package in packages_list:
                if isinstance(package, dict) and "name" in package and "version" in package:
                    packages_dict[package["name"]] = package["version"]

            return packages_dict
        except Exception as err:
            raise Exception(f"Failed to list packages in conda environment. Error: {err}") from err

    @classmethod
    def get_env_type(cls) -> Literal["conda", "mamba", "pip"]:
        """Get the environment type identifier.

        :return: The string "conda"
        :rtype: Literal["conda", "mamba", "pip"]
        """
        return "conda"
