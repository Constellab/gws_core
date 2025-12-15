from datetime import datetime
from enum import Enum

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.credentials.credentials_type import CredentialsDataBasic


class RegisterComposeOptionsRequestDTO(BaseModelDTO):
    """
    DTO for registering compose options

    :param description: Description for the compose
    :type description: str
    :param auto_start: Whether to automatically start the compose on lab start (default: False)
    :type auto_start: bool
    :param environment_variables: Environment variables for the compose
    :type environment_variables: dict[str, str]
    """

    description: str
    auto_start: bool = False
    environment_variables: dict[str, str] | None = None


class RegisterSQLDBComposeRequestOptionsDTO(RegisterComposeOptionsRequestDTO):
    """
    DTO for registering SQLDB compose options (extends RegisterComposeOptionsRequestDTO)

    :param disable_volume_backup: If true, the volume will be placed in a non-backed-up location (default: False)
    :type disable_volume_backup: bool
    :param all_environments_networks: If true, the SQLDB compose will be connected to both prod and dev networks (default: False)
    :type all_environments_networks: bool
    :param volume_sub_directory: Volume directory for the database data (inside the lab volume)
    :type volume_sub_directory: str | None
    """

    disable_volume_backup: bool = False
    all_environments_networks: bool = False
    volume_sub_directory: str | None = None


class StartComposeRequestDTO(BaseModelDTO):
    compose_yaml_content: str  # content of the yaml file
    options: RegisterComposeOptionsRequestDTO


class DockerComposeStatus(str, Enum):
    STOP = "STOP"
    DOWN = "DOWN"
    UP = "UP"
    PARTIALLY_UP = "PARTIALLY_UP"
    ERROR = "ERROR"


class DockerComposeStatusInfoDTO(BaseModelDTO):
    status: DockerComposeStatus
    info: str | None = None


class SubComposeInfoDTO(BaseModelDTO):
    brickName: str
    uniqueName: str
    composeFilePath: str
    composeFileContent: str


class SubComposeListDTO(BaseModelDTO):
    composes: list[SubComposeInfoDTO]


class RegisterSQLDBComposeRequestDTO(BaseModelDTO):
    username: str
    password: str
    database: str
    options: RegisterSQLDBComposeRequestOptionsDTO


class RegisterSQLDBComposeAPIResponseDTO(BaseModelDTO):
    status: DockerComposeStatusInfoDTO
    dbHost: str


class RegisterSQLDBComposeResponseDTO(BaseModelDTO):
    composeStatus: DockerComposeStatusInfoDTO
    credentials: CredentialsDataBasic


class SubComposeProcessStatus(str, Enum):
    """Status for sub compose registration/unregistration processes"""

    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


class SubComposeProcessType(str, Enum):
    """Type of process being performed on a sub compose"""

    REGISTER = "REGISTER"
    UNREGISTER = "UNREGISTER"


class SubComposeProcessInfoDTO(BaseModelDTO):
    """Information about a running/finished process on a sub compose"""

    processType: SubComposeProcessType
    status: SubComposeProcessStatus
    message: str
    startedAt: datetime
    completedAt: datetime | None = None

    def get_duration_seconds(self) -> float | None:
        if self.completedAt:
            return (self.completedAt - self.startedAt).total_seconds()
        return None


class SubComposeStatusDTO(BaseModelDTO):
    """Overall status of a sub compose, including any running process and the docker-compose status"""

    subComposeProcess: SubComposeProcessInfoDTO | None = None
    composeStatus: DockerComposeStatusInfoDTO

    def is_in_progress_status(self) -> bool:
        return (
            self.subComposeProcess is not None
            and self.subComposeProcess.status == SubComposeProcessStatus.RUNNING
        )

    def get_process_message(self) -> str | None:
        if self.subComposeProcess:
            return self.subComposeProcess.message
        return None
