# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import subprocess

from gws_core.impl.file.file_helper import FileHelper

from .base_env_shell import BaseEnvShell


class CondaShellProxy(BaseEnvShell):

    def _install_env(self) -> bool:
        """
        Install an environment from a conda environment file.
        Return true if the env was installed, False if it was already installed.
        """

        cmd = [
            'bash -c "source /opt/conda/etc/profile.d/conda.sh"', "&&",
            f"conda env create -f {self.env_file_path} --force --prefix ./.venv"
        ]

        res: subprocess.CompletedProcess = subprocess.run(
            " ".join(cmd),
            cwd=self.get_env_dir_path(),
            stderr=subprocess.PIPE,
            shell=True
        )

        if res.returncode != 0:
            raise Exception(f"Cannot install the virtual environment. Error: {res.stderr}")

        return True

    def _uninstall_env(self) -> bool:
        """ Uninstall the environment.
        Return true if the env was uninstalled, False if it was already uninstalled.
        """

        cmd = [
            'bash -c "source /opt/conda/etc/profile.d/conda.sh"', "&&",
            "conda remove -y --prefix .venv --all", "&&",
            "cd ..", "&&",
            f"rm -rf {self.get_env_dir_path()}"
        ]

        res: subprocess.CompletedProcess
        try:
            res = subprocess.run(
                " ".join(cmd),
                cwd=self.get_env_dir_path(),
                stderr=subprocess.PIPE,
                shell=True
            )
        except Exception as err:
            try:
                if FileHelper.exists_on_os(self.get_env_dir_path()):
                    FileHelper.delete_dir(self.get_env_dir_path())
                    return True

            except Exception as err:
                raise Exception("Cannot remove the virtual environment.") from err

        if res.returncode != 0:
            raise Exception(f"Cannot remove the virtual environment. Error: {res.stderr}")

        return True

    def format_command(self, user_cmd: list) -> str:
        if isinstance(user_cmd, list):
            user_cmd = [str(c) for c in user_cmd]
            user_cmd = " ".join(user_cmd)
        venv_dir = self.get_venv_dir_path()
        cmd = f'bash -c "source /opt/conda/etc/profile.d/conda.sh && conda activate {venv_dir} && {user_cmd}"'
        return cmd

    def get_venv_dir_path(self) -> str:
        return os.path.join(self.get_env_dir_path(), "./.venv")
