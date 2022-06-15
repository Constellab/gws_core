# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import os
import subprocess

from gws_core.impl.file.file_helper import FileHelper

from .base_env_helper import BaseEnvHelper


class PipEnvHelper(BaseEnvHelper):

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

        pipfile_path = os.path.join(env_dir, "Pipfile")
        cmd = [
            f"cp {env_file_path} {pipfile_path}", "&&",
            "pipenv install", "&&",
            "touch READY"
        ]

        try:
            env = os.environ.copy()
            env["PIPENV_VENV_IN_PROJECT"] = "enabled"
            res = subprocess.run(
                " ".join(cmd),
                cwd=env_dir,
                stderr=subprocess.PIPE,
                env=env,
                shell=True
            )
        except Exception as err:
            raise Exception(
                "Cannot install the virtual environment.") from err

        if res.returncode != 0:
            raise Exception(f"Cannot install the virtual environment. Error: {res.stderr}")

    @classmethod
    def uninstall_env(cls, env_dir: str) -> None:
        if not cls.is_installed(env_dir):
            return

        cmd = [
            "pipenv uninstall --all", "&&",
            "cd ..", "&&",
            f"rm -rf {env_dir}"
        ]

        try:
            env = os.environ.copy()
            env["PIPENV_VENV_IN_PROJECT"] = "enabled"
            res = subprocess.run(
                " ".join(cmd),
                cwd=env_dir,
                stderr=subprocess.DEVNULL,
                env=env,
                shell=True
            )
        except:
            try:
                if FileHelper.exists_on_os(env_dir):
                    FileHelper.delete_dir(env_dir)
            except:
                raise Exception("Cannot remove the virtual environment.")

        if res.returncode != 0:
            raise Exception(f"Cannot remove the virtual environment. Error: {res.stderr}")
