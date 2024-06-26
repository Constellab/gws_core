

from typing import List, Literal

from gws_core.core.model.model_dto import BaseModelDTO


class VEnvCreationInfo(BaseModelDTO):
    file_version: int
    name: str
    hash: str
    created_at: str
    # path of the file that was used to create the env
    origin_env_config_file_path: str
    env_type: Literal['conda', 'mamba', 'pip']


class VEnvBasicInfoDTO(BaseModelDTO):
    folder: str
    name: str
    creation_info: VEnvCreationInfo


class VEnvCompleteInfoDTO(BaseModelDTO):
    basic_info: VEnvBasicInfoDTO
    env_size: int
    config_file_content: str


class VEnsStatusDTO(BaseModelDTO):
    venv_folder: str

    envs: List[VEnvBasicInfoDTO]
