# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import abc
import hashlib
import os
import tempfile

from ....core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ....task.task_decorator import task_decorator
from ...shell.conda_shell_proxy import CondaShellProxy
from .env_live_task import EnvLiveTask


@task_decorator(
    "CondaLiveTask", human_name="Conda live task",
    short_description="Live task to run Python snippets in a conda shell environment. The inputs files are passed to the snippet through the arguments.",
    hide=True)
class CondaLiveTask(EnvLiveTask):
    """
    This task executes Python snippets on the fly in conda shell environments.

    > **Warning**: It is recommended to use code snippets comming from trusted sources.
    """

    @ abc.abstractmethod
    def _format_command(self, code_file_path: str, args: str) -> list:
        pass

    def _create_shell_proxy(self, env: str) -> CondaShellProxy:
        unique_env_dir_name = hashlib.md5(env.encode('utf-8')).hexdigest()
        _, yml_filepath = tempfile.mkstemp(suffix=".yml")
        with open(yml_filepath, 'w', encoding="utf-8") as fp:
            fp.write(env)

        LiveCondaShellProxy = type('LiveCondaShellProxy', (CondaShellProxy,), {})

        proxy = LiveCondaShellProxy(unique_env_dir_name, env_file_path=yml_filepath,
                                    message_dispatcher=self.message_dispatcher)

        self.log_info_message("Installing conda environment ...")
        proxy.install_env()
        self.log_info_message("Done!")

        if not proxy.env_is_installed():
            os.unlink(yml_filepath)
            raise BadRequestException("Cannot install the conda environment")

        return proxy
