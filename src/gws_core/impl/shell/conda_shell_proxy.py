

import os
from typing import Union

from typing_extensions import Literal

from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.shell.virtual_env.venv_dto import VEnvCreationInfo

from .base_env_shell import BaseEnvShell


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

        cmd = [
            self._build_conda_command(self.conda_command,
                                      f'env create -f {self.env_file_path} --force --prefix {self.VENV_DIR_NAME}')
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
            self._build_conda_command(
                self.conda_command,
                f'remove -y --prefix {self.VENV_DIR_NAME} --all && cd .. && rm -rf {self.get_env_dir_path()}')]

        self._message_dispatcher.notify_info_message(
            f"Uninstalling {self.conda_command} env with command: {' '.join(cmd)}.")

        self._execute_uninstall_command(" ".join(cmd))

        return True

    def format_command(self, user_cmd: Union[list, str]) -> str:
        if isinstance(user_cmd, list):
            user_cmd = [str(c) for c in user_cmd]
            user_cmd = " ".join(user_cmd)
        venv_dir = self.get_venv_dir_path()
        # the run command must use conda, not mamba
        cmd = self._build_conda_command(CondaShellProxy.conda_command, f'run -p {venv_dir} {user_cmd}')
        return cmd

    def get_config_file_path(self) -> str:
        return os.path.join(self.get_env_dir_path(), self.CONFIG_FILE_NAME)

    def get_venv_dir_path(self) -> str:
        return os.path.join(self.get_env_dir_path(), self.VENV_DIR_NAME)

    def _build_conda_command(self, conda_cmd: str, cmd: str, ) -> str:
        return f'bash -c "source /opt/conda/etc/profile.d/{CondaShellProxy.conda_command}.sh && {conda_cmd} {cmd}"'

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

            if env_creation_info.env_type != cls.get_env_type():
                return False

            return True
        except:
            return False

    @classmethod
    def get_env_type(cls) -> Literal['conda', 'mamba', 'pip']:
        return 'conda'
