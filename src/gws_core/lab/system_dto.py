

from typing import List, Literal, Optional

from typing_extensions import TypedDict

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.lab.monitor.monitor_dto import MonitorFreeDiskDTO
from gws_core.user.user_dto import SpaceDict

LabEnvironment = Literal["ON_CLOUD", "DESKTOP", "LOCAL"]


class LabInfoDTO(BaseModelDTO):
    id: str
    lab_name: str
    front_version: str
    space: Optional[SpaceDict]


class LabStatusDTO(BaseModelDTO):
    free_disk: MonitorFreeDiskDTO


class SettingsDTO(BaseModelDTO):
    lab_id: str
    lab_name: str
    space_api_url: Optional[str]
    lab_prod_api_url: str
    lab_dev_api_url: str
    lab_environment: str
    virtual_host: str
    main_settings_file_path: str
    log_dir: str
    data_dir: str
    file_store_dir: str
    kv_store_dir: str
    data: dict


class ModuleInfo(TypedDict):
    path: str
    name: str
    source: str
    error: Optional[str]


class BrickMigrationLogHistory(TypedDict):
    version: str
    migration_date: str


class BrickMigrationLog(TypedDict):
    brick_name: str
    version: str
    last_date_check: str
    history: List[BrickMigrationLogHistory]


class PipPackage(BaseModelDTO):
    name: str
    version: str


class LabSystemConfig(BaseModelDTO):
    python_version: str
    pip_packages: List[PipPackage]
