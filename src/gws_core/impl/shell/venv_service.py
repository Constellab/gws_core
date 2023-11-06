# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from typing import List

from typing_extensions import TypedDict

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.shell.base_env_shell import BaseEnvShell, VEnvCreationInfo
from gws_core.impl.shell.conda_shell_proxy import CondaShellProxy
from gws_core.impl.shell.mamba_shell_proxy import MambaShellProxy
from gws_core.impl.shell.pip_shell_proxy import PipShellProxy


class VEnvBasicInfo(TypedDict):
    folder: str
    name: str
    creation_info: VEnvCreationInfo


class VEnvCompleteInfo(TypedDict):
    basic_info: VEnvBasicInfo
    env_size: int
    config_file_content: str


class VEnsStatus(TypedDict):
    venv_folder: str

    envs: List[VEnvBasicInfo]


class VEnvService():
    """
    Service to manager, list and delete virtual environments.
    """

    @classmethod
    def get_vens_status(cls) -> VEnsStatus:
        """
        Get the status of the virtual environments.
        """
        if not FileHelper.exists_on_os(Settings.get_global_env_dir()):
            FileHelper.create_dir_if_not_exist(Settings.get_global_env_dir())

        venv_status: VEnsStatus = {
            'venv_folder': Settings.get_global_env_dir(),
            'envs': [],
        }

        for node_name in os.listdir(Settings.get_global_env_dir()):

            # check if it's a conda env
            folder_path = os.path.join(Settings.get_global_env_dir(), node_name)

            # keep only the folder
            if not FileHelper.is_dir(folder_path):
                continue

            try:
                env_info = cls.get_venv_basic_info(node_name)
                venv_status['envs'].append(env_info)
            except:
                Logger.error(f'Error while getting the env info of env {folder_path}')

        return venv_status

    @classmethod
    def get_venv_complete_info(cls, venv_name: str) -> VEnvCompleteInfo:
        """
        Get the information of a virtual environment.
        """
        venv_path = os.path.join(Settings.get_global_env_dir(), venv_name)

        if not FileHelper.is_dir(venv_path):
            raise ValueError(f'Venv {venv_name} does not exist.')

        config_file_path: str

        if PipShellProxy.folder_is_env(venv_path):
            config_file_path = os.path.join(venv_path, PipShellProxy.CONFIG_FILE_NAME)
        elif MambaShellProxy.folder_is_env(venv_path):
            config_file_path = os.path.join(venv_path, CondaShellProxy.CONFIG_FILE_NAME)
        elif CondaShellProxy.folder_is_env(venv_path):
            config_file_path = os.path.join(venv_path, CondaShellProxy.CONFIG_FILE_NAME)
        else:
            raise ValueError(f'Venv {venv_name} is not a valid venv.')

        # read the config file
        with open(config_file_path, 'r+', encoding='UTF-8') as fp:
            config_file_content = fp.read()

        return {
            'basic_info': cls.get_venv_basic_info(venv_name),
            'env_size': FileHelper.get_size(os.path.join(venv_path,
                                                         BaseEnvShell.VENV_DIR_NAME)),
            'config_file_content': config_file_content
        }

    @classmethod
    def get_venv_basic_info(cls, venv_name: str) -> VEnvBasicInfo:
        """
        Get the information of a virtual environment.
        """
        venv_path = os.path.join(Settings.get_global_env_dir(), venv_name)

        if not FileHelper.is_dir(venv_path):
            raise ValueError(f'Venv {venv_name} does not exist.')

        env_creation_info: VEnvCreationInfo = BaseEnvShell.get_creation_info(venv_path)

        return {
            'name': venv_name,
            'folder': venv_path,
            'creation_info': env_creation_info,
        }

    @classmethod
    def delete_venv(cls, venv_name: str, check_running_experiment: bool = False) -> None:
        """
        Delete a virtual environment.
        """
        if check_running_experiment and ExperimentService.count_of_running_experiments() > 0:
            raise BadRequestException('Cannot delete a venv while an experiment is running.')
        venv_folder = os.path.join(Settings.get_global_env_dir(), venv_name)
        FileHelper.delete_dir(venv_folder)

    @classmethod
    def delete_all_venvs(cls) -> None:
        """
        Delete all virtual environments.
        """
        if ExperimentService.count_of_running_experiments() > 0:
            raise BadRequestException('Cannot delete a venv while an experiment is running.')
        FileHelper.delete_dir_content(Settings.get_global_env_dir())
