

from typing import Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.user.user_dto import SpaceDict


class LabInfoDTO(BaseModelDTO):
    id: str
    lab_name: str
    front_version: str
    space: Optional[SpaceDict]


class SettingsDTO(BaseModelDTO):
    lab_id: str
    lab_name: str
    space_api_url: Optional[str]
    lab_prod_api_url: str
    lab_dev_api_url: str
    lab_environment: str
    virtual_host: str
    cwd: str
    log_dir: str
    data_dir: str
    file_store_dir: str
    kv_store_dir: str
    data: dict
