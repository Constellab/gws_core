from typing import Any, Dict, List, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.io.io_spec import IOSpecDTO


class CommunityLiveTaskSpaceDTO(BaseModelDTO):
    id: str
    name: str


class CommunityLiveTaskDTO(BaseModelDTO):
    id: str
    title: str
    space: Optional[CommunityLiveTaskSpaceDTO] = None
    created_at: Optional[str] = None
    last_modified_at: Optional[str] = None
    created_by: Optional[object] = None
    latest_publish_version: int
    description: Optional[object] = None


class CommunityLiveTaskIOSpecDTO(BaseModelDTO):
    # TODO type to improve, it is not standard
    specs: Dict[str, IOSpecDTO]


class CommunityLiveTaskVersionDTO(BaseModelDTO):
    id: str
    version: int
    type: str
    environment: Optional[str]
    params: Optional[List[str]]
    code: str
    input_specs: Optional[CommunityLiveTaskIOSpecDTO]
    output_specs: Optional[CommunityLiveTaskIOSpecDTO]
    config_specs: Optional[Dict]
    live_task: CommunityLiveTaskDTO


class CommunityCreateLiveTaskDTO(BaseModelDTO):
    title: str
    type: str
    space: Any


class CommunityGetLiveTasksBody(BaseModelDTO):
    spacesFilter: List[str] = []
    titleFilter: str = ''
    personalOnly: bool = False


class CommunityLiveTaskVersionCreateResDTO(BaseModelDTO):
    id: str
    live_task_version: str
