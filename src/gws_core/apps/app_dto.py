
from enum import Enum
from typing import Dict, List, Literal, Optional

from gws_core.core.model.model_dto import BaseModelDTO


class AppType(Enum):
    STREAMLIT = "STREAMLIT"
    REFLEX = "REFLEX"


class AppInstanceUrl(BaseModelDTO):
    host_url: str

    params: Optional[Dict[str, str]] = None

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
    app_config_path: str
    env_type: str
    source_ids: List[str] = None
    env_file_path: Optional[str] = None  # for env app
    env_file_content: Optional[str] = None  # for env app


class AppProcessStatus(Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"


class CreateAppAsyncResultDTO(BaseModelDTO):
    app_id: str
    app_url: AppInstanceUrl
    get_status_route: str
    status: AppProcessStatus
    status_text: Optional[str] = None


class AppProcessStatusDTO(BaseModelDTO):
    id: str
    status: AppProcessStatus
    status_text: Optional[str] = None
    running_apps: List[AppInstanceDTO]
    nb_of_connections: int


class AppsStatusDTO(BaseModelDTO):
    processes: List[AppProcessStatusDTO]


class AppInstanceConfigDTO(BaseModelDTO):
    app_dir_path: str
    source_ids: List[str]
    params: Optional[dict]
    requires_authentication: bool
    # List of token of user that can access the app
    # Only provided if the app requires authentication
    # Key is access token, value is user id
    user_access_tokens: Dict[str, str]
