# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import hashlib
import os
import tempfile

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException

from ..conda_shell_proxy import CondaShellProxy
from ..pip_shell_proxy import PipShellProxy


class EnvShellProxyHelper():
    """
    An helper to easily create env shell proxies using configuration data
    """

    @staticmethod
    def create_conda_shell_proxy(env_confg_data: str, message_dispatcher: MessageDispatcher = None) -> CondaShellProxy:
        """
        Create a CondaShellProxy using `env_confg_data`

        A temporary .yml file is created using the `env_confg_data` and the corresponding CondaShellProxy is created.
        The folder of the CondaShellProxy is uniquly generated using the md5 hash of the `env_confg_data`.
        """

        unique_env_dir_name = hashlib.md5(env_confg_data.encode('utf-8')).hexdigest()
        _, yml_filepath = tempfile.mkstemp(suffix=".yml")
        with open(yml_filepath, 'w', encoding="utf-8") as fp:
            fp.write(env_confg_data)

        LiveCondaShellProxy = type('LiveCondaShellProxy', (CondaShellProxy,), {})

        proxy = LiveCondaShellProxy(unique_env_dir_name, env_file_path=yml_filepath,
                                    message_dispatcher=message_dispatcher)

        proxy.log_info_message("Installing conda environment ...")
        proxy.install_env()
        proxy.log_info_message("Done!")

        if not proxy.env_is_installed():
            os.unlink(yml_filepath)
            raise BadRequestException("Cannot install the conda environment")

        return proxy

    @staticmethod
    def create_pipenv_shell_proxy(env_confg_data: str, message_dispatcher: MessageDispatcher = None) -> PipShellProxy:
        """
        Create a PipShellProxy using `env_confg_data`

        A temporary .yml file is created using the `env_confg_data` and the corresponding PipShellProxy is created.
        The folder of the PipShellProxy is uniquly generated using the md5 hash of the `env_confg_data`.
        """

        unique_env_dir_name = hashlib.md5(env_confg_data.encode('utf-8')).hexdigest()
        _, yml_filepath = tempfile.mkstemp(suffix=".yml")
        with open(yml_filepath, 'w', encoding="utf-8") as fp:
            fp.write(env_confg_data)

        LivePipenvShellProxy = type('LivePipenvShellProxy', (PipShellProxy,), {})

        proxy = LivePipenvShellProxy(unique_env_dir_name, env_file_path=yml_filepath,
                                     message_dispatcher=message_dispatcher)

        proxy.log_info_message("Installing pip environment ...")
        proxy.install_env()
        proxy.log_info_message("Done!")

        if not proxy.env_is_installed():
            os.unlink(yml_filepath)
            raise BadRequestException("Cannot install the pip environment")

        return proxy
