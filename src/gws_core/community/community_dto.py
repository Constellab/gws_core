from gws_core.core.model.model_dto import BaseModelDTO
from typing import Dict, Optional, List, Any

class CommunityLiveTaskSpaceDTO(BaseModelDTO):
    id: str
    name: str

class CommunityLiveTaskDTO(BaseModelDTO):
    id: str
    title: str
    space: Optional[CommunityLiveTaskSpaceDTO]
    created_at: Optional[str]
    last_modified_at: Optional[str]
    created_by: Optional[object]
    latest_publish_version: int
    description: Optional[object]

class CommunityLiveTaskVersionDTO(BaseModelDTO):
    id: str
    version: int
    type: str
    environment: Optional[str]
    params: Optional[List[str]]
    code: str
    input_specs: Dict
    output_specs: Dict
    config_specs: Dict
    live_task: CommunityLiveTaskDTO

class CommunityCreateLiveTaskDTO(BaseModelDTO):
    title: str
    type: str
    space: Any

class CommunityLiveTaskVersionCreateResDTO(BaseModelDTO):
    id: str
    live_task_version: str