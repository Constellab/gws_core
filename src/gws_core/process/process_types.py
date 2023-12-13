# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Optional

from typing_extensions import TypedDict

from gws_core.config.config_dto import ConfigSimpleDTO
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.io.io_dto import IODTO

if TYPE_CHECKING:
    from gws_core.protocol.protocol_dto import ProtocolConfigDTO


class ProcessStatus(Enum):
    DRAFT = "DRAFT"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"
    # For protocol, it means that some process of protocol were not run (or added after run)
    PARTIALLY_RUN = "PARTIALLY_RUN"
    WAITING_FOR_CLI_PROCESS = "WAITING_FOR_CLI_PROCESS"


class ProcessErrorInfo(TypedDict):
    detail: str
    unique_code: str
    context: str
    instance_id: str


class ProcessMinimumDTO(BaseModelDTO):
    id: str
    process_typing_name: str


class ProcessConfigDTO(BaseModelDTO):
    process_typing_name: str
    instance_name: str
    config: ConfigSimpleDTO
    human_name: Optional[str]
    short_description: Optional[str]
    brick_version: str
    inputs: IODTO
    outputs: IODTO
    status: str
    # for sub protocol, recursive graph
    graph: Optional['ProtocolConfigDTO'] = None
