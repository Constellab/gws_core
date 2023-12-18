# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

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


class ProcessErrorInfo(BaseModelDTO):
    detail: str
    unique_code: Optional[str]
    context: Optional[str]
    instance_id: Optional[str]


class ProcessMinimumDTO(BaseModelDTO):
    id: str
    process_typing_name: str
