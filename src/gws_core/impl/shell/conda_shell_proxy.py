# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import subprocess
from typing import Union, final

from gws_core.impl.file.file_helper import FileHelper

from .base_env_shell import BaseEnvShell


class CondaShellProxy(BaseEnvShell):

    CONFIG_FILE_NAME = "environment.yml"

    def _install_env(self) -> bool:
        """
        Install an environment from a conda environment file.
        Return true if the env was installed, False if it was already installed.
        """

        cmd = [
            f'bash -c "source /opt/conda/etc/profile.d/conda.sh && conda env create -f \
{self.env_file_path} --force --prefix {self.VENV_DIR_NAME}"'
        ]

        res: subprocess.CompletedProcess = subprocess.run(
            " ".join(cmd),
            cwd=self.get_env_dir_path(),
            stderr=subprocess.PIPE,
            shell=True,
            check=False
        )

        if res.returncode != 0:
            self._message_dispatcher.notify_error_message(res.stderr.decode('utf-8'))
            raise Exception(f"Cannot install the virtual environment. Error: {res.stderr}")

        # copy the file the was used to create the env into the env dir
        env_file_path = os.path.join(self.get_env_dir_path(), self.CONFIG_FILE_NAME)
        FileHelper.copy_file(self.env_file_path, env_file_path)

        return True

    def _uninstall_env(self) -> bool:
        """ Uninstall the environment.
        Return true if the env was uninstalled, False if it was already uninstalled.
        """

        cmd = [
            f'bash -c "source /opt/conda/etc/profile.d/conda.sh && \
conda remove -y --prefix {self.VENV_DIR_NAME} --all && \
cd .. && rm -rf {self.get_env_dir_path()}"'
        ]

        res = subprocess.run(
            " ".join(cmd),
            cwd=self.get_env_dir_path(),
            stderr=subprocess.PIPE,
            shell=True,
            check=False
        )
        if res.returncode != 0:
            try:
                if FileHelper.exists_on_os(self.get_env_dir_path()):
                    FileHelper.delete_dir(self.get_env_dir_path())
                    return True

            except Exception as err:
                raise Exception("Cannot remove the virtual environment.") from err

        return True

    def format_command(self, user_cmd: Union[list, str]) -> str:
        if isinstance(user_cmd, list):
            user_cmd = [str(c) for c in user_cmd]
            user_cmd = " ".join(user_cmd)
        venv_dir = self.get_venv_dir_path()
        cmd = f'bash -c "source /opt/conda/etc/profile.d/conda.sh && conda activate {venv_dir} && {user_cmd}"'
        return cmd

    def get_config_file_path(self) -> str:
        return os.path.join(self.get_env_dir_path(), self.CONFIG_FILE_NAME)

    def get_venv_dir_path(self) -> str:
        return os.path.join(self.get_env_dir_path(), self.VENV_DIR_NAME)

    @final
    def run(self, cmd: Union[list, str], env: dict = None, shell_mode=True) -> None:
        return super().run(cmd, env, shell_mode=shell_mode)

    @classmethod
    def folder_is_env(cls, folder_path: str) -> bool:
        """return true if the folder is a valid env folder"""

        pipfile_path = os.path.join(folder_path, cls.CONFIG_FILE_NAME)
        sub_venv_path = os.path.join(folder_path, cls.VENV_DIR_NAME)

        return super().folder_is_env(folder_path) and \
            FileHelper.exists_on_os(pipfile_path) and \
            FileHelper.exists_on_os(sub_venv_path)
