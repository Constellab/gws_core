# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
import os
import subprocess

from gws_core.impl.file.file_helper import FileHelper

from .base_env import BaseEnv


class PipEnv(BaseEnv):

    def _install(self) -> bool:
        """
        Install an environment from a conda environment file.
        Return true if the env was installed, False if it was already installed.
        """

        pipfile_path = self.get_pip_file_path()
        cmd = [
            f"cp {self.env_file_path} {pipfile_path}", "&&",
            "pipenv install"
        ]

        env = os.environ.copy()
        env["PIPENV_VENV_IN_PROJECT"] = "enabled"
        res = subprocess.run(
            " ".join(cmd),
            cwd=self.get_env_dir_path(),
            stderr=subprocess.PIPE,
            env=env,
            shell=True
        )

        if res.returncode != 0:
            raise Exception(f"Cannot install the virtual environment. Error: {res.stderr}")

        return True

    def uninstall(self) -> bool:
        """ Uninstall the environment.
        Return true if the env was uninstalled, False if it was already uninstalled.
        """

        cmd = [
            "pipenv uninstall --all", "&&",
            "cd ..", "&&",
            f"rm -rf {self.get_env_dir_path()}"
        ]

        try:
            env = os.environ.copy()
            env["PIPENV_VENV_IN_PROJECT"] = "enabled"
            res = subprocess.run(
                " ".join(cmd),
                cwd=self.get_env_dir_path(),
                stderr=subprocess.DEVNULL,
                env=env,
                shell=True
            )
        except:
            try:
                if FileHelper.exists_on_os(self.get_env_dir_path()):
                    FileHelper.delete_dir(self.get_env_dir_path())
                    return True
            except:
                raise Exception("Cannot remove the virtual environment.")

        if res.returncode != 0:
            raise Exception(f"Cannot remove the virtual environment. Error: {res.stderr}")

        return True

    def format_command(self, user_cmd: list) -> str:
        """
        This method builds the command to execute.

        :return: The list of arguments used to build the final command in the Python method `subprocess.run`
        :rtype: `list`
        """

        if isinstance(user_cmd, list):
            user_cmd = [str(c) for c in user_cmd]
        if user_cmd[0] in ["python", "python2", "python3"]:
            del user_cmd[0]
        user_cmd = ["pipenv", "run", "python", *user_cmd]
        cmd = " ".join(user_cmd)
        return cmd

    def build_os_env(self) -> dict:
        env = os.environ.copy()
        pipfile_path = self.get_pip_file_path()
        env["PIPENV_PIPFILE"] = pipfile_path
        env["PIPENV_VENV_IN_PROJECT"] = "enabled"
        return env

    def get_pip_file_path(self) -> str:
        return os.path.join(self.get_env_dir_path(), "Pipfile")
