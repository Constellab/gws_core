
from enum import Enum
from typing import Dict, List, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.credentials.credentials_type import CredentialsDataBasic


class StartComposeRequestDTO(BaseModelDTO):
    compose_yaml_content: str  # content of the yaml file
    description: str
    env: Optional[Dict[str, str]] | None = None
    auto_start: bool = False


class DockerComposeStatus(str, Enum):
    STOP = "STOP"
    DOWN = "DOWN"
    UP = "UP"
    PARTIALLY_UP = "PARTIALLY_UP"
    ERROR = "ERROR"


class DockerComposeStatusInfoDTO(BaseModelDTO):
    status: DockerComposeStatus
    info: Optional[str] = None

    def is_in_progress_status(self) -> bool:
        return False


class SubComposeInfoDTO(BaseModelDTO):
    brickName: str
    uniqueName: str
    composeFilePath: str
    composeFileContent: str


class SubComposeListDTO(BaseModelDTO):
    composes: List[SubComposeInfoDTO]


class RegisterSQLDBComposeRequestDTO(BaseModelDTO):
    username: str
    password: str
    database: str
    description: str
    env: Optional[Dict[str, str]] | None = None
    auto_start: bool = False


class RegisterSQLDBComposeAPIResponseDTO(BaseModelDTO):
    status: DockerComposeStatusInfoDTO
    dbHost: str


class RegisterSQLDBComposeResponseDTO(BaseModelDTO):
    composeStatus: DockerComposeStatusInfoDTO
    credentials: CredentialsDataBasic
