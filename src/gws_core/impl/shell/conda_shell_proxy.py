

import os
from typing import List, Union

from typing_extensions import Literal

from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.shell.virtual_env.venv_dto import VEnvCreationInfo
from gws_core.model.typing_register_decorator import typing_registrator

from .base_env_shell import BaseEnvShell


@typing_registrator(unique_name="CondaShellProxy", object_type="MODEL", hide=True)
class CondaShellProxy(BaseEnvShell):

    CONFIG_FILE_NAME = "environment.yml"

    # can be overridden by the child class to use mamba instead of conda
    # the mamba command is only used for install and uninstall the env
    conda_command = "conda"

    def _install_env(self) -> bool:
        """
        Install an environment from a conda environment file.
        Return true if the env was installed, False if it was already installed.
        """

        # --prefix define the path where the env will be created relative to where the
        # command is executed. Command is executed in the env dir, so the path is relative to that.
        cmd = [
            self._build_str_conda_command(self.conda_command,
                                          f'env create -f {self.env_file_path} --yes --prefix ./{self.VENV_DIR_NAME}')
        ]

        self._message_dispatcher.notify_info_message(
            f"Installing {self.conda_command} env with command: {' '.join(cmd)}.")

        self._execute_env_install_command(" ".join(cmd))

        # copy the file the was used to create the env into the env dir
        env_file_path = os.path.join(
            self.get_env_dir_path(), self.CONFIG_FILE_NAME)
        FileHelper.copy_file(self.env_file_path, env_file_path)

        return True

    def _uninstall_env(self) -> bool:
        """ Uninstall the environment.
        Return true if the env was uninstalled, False if it was already uninstalled.
        """

        cmd = [
            self._build_str_conda_command(
                self.conda_command,
                f'remove -y --prefix {self.VENV_DIR_NAME} --all && cd .. && rm -rf {self.get_env_dir_path()}')]

        self._message_dispatcher.notify_info_message(
            f"Uninstalling {self.conda_command} env with command: {' '.join(cmd)}.")

        self._execute_uninstall_command(" ".join(cmd))

        return True

    def format_command(self, user_cmd: Union[list, str]) -> Union[list, str]:
        is_list = isinstance(user_cmd, list)

        str_cmd: str = None
        if is_list:
            str_cmd = " ".join([str(c) for c in user_cmd])
        else:
            str_cmd = str(user_cmd)

        str_cmd = f'activate {self.get_venv_dir_path()} && {str_cmd}'

        # the run command must use conda, not mamba
        # use conda activate and not run, otherwise the logs are retrieve only after the command is finished (not in real time)
        if is_list:
            return self._build_list_conda_command(CondaShellProxy.conda_command, str_cmd)
        else:
            return self._build_str_conda_command(CondaShellProxy.conda_command, str_cmd)

    def get_default_env_variables(self) -> dict:
        """
        Creates the OS environment variables that are passed to the shell command

        :return: The OS environment variables
        :rtype: `dict`
        """

        # PYTHONUNBUFFERED is used to force the python output to be unbuffered so the log are in real time
        # (this needs to be with conda activate to be log in real time)
        return {'PYTHONUNBUFFERED': '1'}

    def get_config_file_path(self) -> str:
        return os.path.join(self.get_env_dir_path(), self.CONFIG_FILE_NAME)

    def get_venv_dir_path(self) -> str:
        return os.path.join(self.get_env_dir_path(), self.VENV_DIR_NAME)

    def _build_str_conda_command(self, conda_cmd: str, cmd: str) -> str:
        return f'bash -c "{self._build_sub_conda_command(conda_cmd, cmd)}"'

    def _build_list_conda_command(self, conda_cmd: str, cmd: str) -> List[str]:
        return ['bash', '-c', self._build_sub_conda_command(conda_cmd, cmd)]

    def _build_sub_conda_command(self, conda_cmd: str, cmd: str) -> str:
        return f'source /opt/conda/etc/profile.d/{CondaShellProxy.conda_command}.sh && {conda_cmd} {cmd}'

    @classmethod
    def folder_is_env(cls, folder_path: str) -> bool:
        """return true if the folder is a valid env folder"""

        pipfile_path = os.path.join(folder_path, cls.CONFIG_FILE_NAME)
        sub_venv_path = os.path.join(folder_path, cls.VENV_DIR_NAME)

        if not super().folder_is_env(folder_path) or \
           not FileHelper.exists_on_os(pipfile_path) or \
           not FileHelper.exists_on_os(sub_venv_path):
            return False

        try:
            env_creation_info: VEnvCreationInfo = cls.get_creation_info(folder_path)

            if env_creation_info.env_type in ['conda', 'mamba']:
                return True
            else:
                return False
        except:
            return False

    @classmethod
    def get_env_type(cls) -> Literal['conda', 'mamba', 'pip']:
        return 'conda'
