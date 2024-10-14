from typing import Any, Dict, List, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.io.io_spec import IOSpecDTO


class CommunityAgentSpaceDTO(BaseModelDTO):
    id: str
    name: str


class CommunityAgentDTO(BaseModelDTO):
    id: str
    title: str
    space: Optional[CommunityAgentSpaceDTO] = None
    created_at: Optional[str] = None
    last_modified_at: Optional[str] = None
    created_by: Optional[object] = None
    latest_publish_version: int
    description: Optional[object] = None


class CommunityAgentIOSpecDTO(BaseModelDTO):
    # TODO type to improve, it is not standard
    specs: Dict[str, IOSpecDTO]


class CommunityAgentVersionDTO(BaseModelDTO):
    id: str
    version: int
    type: str
    environment: Optional[str]
    params: Optional[str]
    code: str
    input_specs: Optional[CommunityAgentIOSpecDTO]
    output_specs: Optional[CommunityAgentIOSpecDTO]
    config_specs: Optional[Dict]
    agent: CommunityAgentDTO


class CommunityCreateAgentDTO(BaseModelDTO):
    title: str
    type: str
    space: Any


class CommunityGetAgentsBody(BaseModelDTO):
    spacesFilter: List[str] = []
    titleFilter: str = ''
    personalOnly: bool = False


class CommunityAgentVersionCreateResDTO(BaseModelDTO):
    id: str
    agent_version: str
    title: str
