

from typing import Dict, List, Literal, Optional

from gws_core.core.model.model_dto import BaseModelDTO


class StreamlitAppDTO(BaseModelDTO):
    resource_id: str
    url: str
    streamlit_app_config_path: str
    source_paths: List[str]


class StreamlitProcessStatusDTO(BaseModelDTO):
    id: str
    status: Literal["RUNNING", "STOPPED"]
    running_apps: List[StreamlitAppDTO]
    nb_of_connections: int


class StreamlitStatusDTO(BaseModelDTO):
    processes: List[StreamlitProcessStatusDTO]


class StreamlitConfigDTO(BaseModelDTO):
    app_dir_path: str
    source_ids: List[str]
    params: Optional[dict]
    requires_authentication: bool
    # List of token of user that can access the app
    # Only provided if the app requires authentication
    # Key is access token, value is user id
    user_access_tokens: Dict[str, str]
