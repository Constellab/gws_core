
from typing import List, Optional
from enum import Enum

from gws_core.core.model.model_dto import BaseModelDTO


class StartComposeRequestDTO(BaseModelDTO):
    composeContent: str


class DockerComposeResponseDTO(BaseModelDTO):
    message: str
    output: str


class DockerComposeStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"
    NOT_FOUND = "not_found"


class DockerComposeStatusInfoDTO(BaseModelDTO):
    status: DockerComposeStatus
    info: Optional[str] = None


class SubComposeInfoDTO(BaseModelDTO):
    brickName: str
    uniqueName: str
    composeFilePath: str
    composeFileContent: str


class SubComposeListDTO(BaseModelDTO):
    composes: List[SubComposeInfoDTO]