from datetime import datetime, timezone

from typing_extensions import TypedDict

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.settings_dto import PipPackage
from gws_core.lab.lab_model.lab_dto import LabDTO
from gws_core.lab.monitor.monitor_dto import MonitorFreeDiskDTO


class LabSystemInfoDTO(BaseModelDTO):
    lab: LabDTO
    front_version: str


class LabStatusDTO(BaseModelDTO):
    free_disk: MonitorFreeDiskDTO
    has_start_error: bool


class LabSystemConfig(BaseModelDTO):
    python_version: str
    pip_packages: list[PipPackage]


class LabStartLogFileObject(BaseModelDTO):
    progress: dict
    main_errors: list[str]
    errors: list[str]

    def has_main_errors(self) -> bool:
        return len(self.main_errors) > 0
