# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import subprocess

from gws_core.impl.file.file_helper import FileHelper

from .base_env_helper import BaseEnvHelper


class CondaHelper(BaseEnvHelper):

    @classmethod
    def install_env(cls, env_file_path: str, env_dir: str) -> None:
        """
        Install an environment from a conda environment file.
        """
        if cls.is_installed(env_dir):
            return

        if isinstance(env_file_path, str):
            if not FileHelper.exists_on_os(env_file_path):
                raise Exception(
                    f"The environment file '{env_file_path}' does not exist")
        else:
            raise Exception("Invalid env file path")
        cmd = [
            'bash -c "source /opt/conda/etc/profile.d/conda.sh"', "&&",
            f"conda env create -f {env_file_path} --force --prefix ./.venv", "&&",
            "touch READY",
        ]

        res: subprocess.CompletedProcess
        try:

            res = subprocess.run(
                " ".join(cmd),
                cwd=env_dir,
                stderr=subprocess.PIPE,
                shell=True
            )
        except Exception as err:
            raise Exception("Cannot install the virtual environment.") from err

        if res.returncode != 0:
            raise Exception(f"Cannot install the virtual environment. Error: {res.stderr}")

    @classmethod
    def uninstall_env(cls, env_dir: str) -> None:
        if not cls.is_installed(env_dir):
            return
        cmd = [
            'bash -c "source /opt/conda/etc/profile.d/conda.sh"', "&&",
            "conda remove -y --prefix .venv --all", "&&",
            "cd ..", "&&",
            f"rm -rf {env_dir}"
        ]

        res: subprocess.CompletedProcess
        try:
            res = subprocess.run(
                " ".join(cmd),
                cwd=env_dir,
                stderr=subprocess.PIPE,
                shell=True
            )
        except Exception as err:
            try:
                if FileHelper.exists_on_os(env_dir):
                    FileHelper.delete_dir(env_dir)
            except Exception as err:
                raise Exception("Cannot remove the virtual environment.") from err

        if res.returncode != 0:
            raise Exception(f"Cannot remove the virtual environment. Error: {res.stderr}")
