from typing import Literal

from gws_core.core.model.model_dto import BaseModelDTO


class VEnvCreationInfo(BaseModelDTO):
    """Information about the creation of a virtual environment.

    This metadata is stored in the environment directory to track when and how
    the environment was created.
    """

    file_version: int
    name: str
    hash: str
    created_at: str
    # path of the file that was used to create the env
    origin_env_config_file_path: str
    env_type: Literal["conda", "mamba", "pip"]


class VEnvBasicInfoDTO(BaseModelDTO):
    """Basic information about a virtual environment.

    Includes the folder location, name, and creation metadata.
    """

    folder: str
    name: str
    creation_info: VEnvCreationInfo


class VEnvCompleteInfoDTO(BaseModelDTO):
    """Complete information about a virtual environment.

    Extends basic info with the environment size and the content of the
    configuration file used to create it.
    """

    basic_info: VEnvBasicInfoDTO
    env_size: int
    config_file_content: str


class VEnsStatusDTO(BaseModelDTO):
    """Status information for all virtual environments.

    Contains the global virtual environment folder path and a list of all
    managed environments.
    """

    venv_folder: str

    envs: list[VEnvBasicInfoDTO]


class VEnvPackagesDTO(BaseModelDTO):
    """Package list for a virtual environment.

    Contains a dictionary mapping package names to their installed versions.
    """

    packages: dict[str, str]
