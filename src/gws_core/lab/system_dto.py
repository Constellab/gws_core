from typing import Literal

from typing_extensions import TypedDict

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.lab.monitor.monitor_dto import MonitorFreeDiskDTO
from gws_core.user.user_dto import SpaceDict

LabEnvironment = Literal["ON_CLOUD", "DESKTOP", "LOCAL"]


class LabInfoDTO(BaseModelDTO):
    id: str
    lab_name: str
    front_version: str
    space: SpaceDict | None


class LabStatusDTO(BaseModelDTO):
    free_disk: MonitorFreeDiskDTO
    has_start_error: bool


class SettingsDTO(BaseModelDTO):
    lab_id: str
    lab_name: str
    space_api_url: str | None
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
    error: str | None


class BrickMigrationLogHistory(TypedDict):
    version: str
    migration_date: str


class BrickMigrationLog(TypedDict):
    brick_name: str
    version: str | None
    last_date_check: str | None
    history: list[BrickMigrationLogHistory]
    db_manager_unique_name: str


class PipPackage(BaseModelDTO):
    name: str
    version: str


class LabSystemConfig(BaseModelDTO):
    python_version: str
    pip_packages: list[PipPackage]


class LabStartLogFileObject(BaseModelDTO):
    progress: dict
    main_errors: list[str]
    errors: list[str]

    def has_main_errors(self) -> bool:
        return len(self.main_errors) > 0
