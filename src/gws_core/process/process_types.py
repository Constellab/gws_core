

from __future__ import annotations

from enum import Enum
from typing import Optional

from gws_core.core.model.model_dto import BaseModelDTO


class ProcessStatus(Enum):
    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    # For protocol, it means that some process of protocol were not run (or added after run)
    PARTIALLY_RUN = "PARTIALLY_RUN"
    WAITING_FOR_CLI_PROCESS = "WAITING_FOR_CLI_PROCESS"

    @classmethod
    def from_str(cls, status: str) -> ProcessStatus:
        return ProcessStatus[status.upper()]


class ProcessErrorInfo(BaseModelDTO):
    detail: str
    unique_code: Optional[str]
    context: Optional[str]
    instance_id: Optional[str]


class ProcessMinimumDTO(BaseModelDTO):
    id: str
    process_typing_name: str
