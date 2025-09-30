
from enum import Enum
from typing import List, Literal, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.credentials.credentials_type import CredentialsDataBasic


class StartComposeRequestDTO(BaseModelDTO):
    composeContent: str  # content of the yaml file
    description: str


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
    host: str
    username: str
    password: str
    database: str
    description: str
    env: Literal['prod', 'dev', 'test']


class RegisterSQLDBComposeResponseDTO(BaseModelDTO):
    composeStatus: DockerComposeStatusInfoDTO
    credentials: CredentialsDataBasic
