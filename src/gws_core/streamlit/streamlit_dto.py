

from typing import List, Literal

from gws_core.core.model.model_dto import BaseModelDTO


class StreamlitAppDTO(BaseModelDTO):
    resource_id: str
    url: str
    streamlit_app_code_path: str
    source_paths: List[str]


class StreamlitStatusDTO(BaseModelDTO):
    status: Literal["RUNNING", "STOPPED"]
    running_apps: List[StreamlitAppDTO]
    nb_of_connections: int
