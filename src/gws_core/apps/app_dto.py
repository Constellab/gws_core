from datetime import datetime
from enum import Enum

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.user.user_dto import UserDTO


class AppType(Enum):
    STREAMLIT = "STREAMLIT"
    REFLEX = "REFLEX"


class AppInstanceUrl(BaseModelDTO):
    host_url: str

    params: dict[str, str] | None = None

    def get_url(self) -> str:
        url = self.host_url

        if self.params is not None and len(self.params) > 0:
            params = "&".join([f"{key}={value}" for key, value in self.params.items()])
            url += f"?{params}"
        return url

    def add_param(self, key: str, value: str) -> None:
        if self.params is None:
            self.params = {}
        self.params[key] = value


class AppInstanceDTO(BaseModelDTO):
    app_type: AppType
    app_resource_id: str
    name: str
    env_type: str
    source_ids: list[str] | None = None
    env_file_path: str | None = None  # for env app
    env_file_content: str | None = None  # for env app


class AppProcessStatus(Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"


class CreateAppAsyncResultDTO(BaseModelDTO):
    app_id: str
    app_url: AppInstanceUrl
    get_status_route: str
    status: AppProcessStatus
    status_text: str | None = None


class AppProcessStatusDTO(BaseModelDTO):
    id: str
    status: AppProcessStatus
    status_text: str | None = None
    app: AppInstanceDTO
    nb_of_connections: int
    config_file_path: str
    started_at: datetime | None
    started_by: UserDTO | None


class AppsStatusDTO(BaseModelDTO):
    processes: list[AppProcessStatusDTO]


class AppInstanceConfigDTO(BaseModelDTO):
    source_ids: list[str]
    params: dict | None
    # List of token of user that can access the app
    # Only provided if the app requires authentication
    # Key is access token, value is user id
    user_access_tokens: dict[str, str]
