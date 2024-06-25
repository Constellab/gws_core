from typing import Any, Dict, List, Optional

from gws_core.core.model.model_dto import BaseModelDTO


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


class CommunityLiveTaskVersionDTO(BaseModelDTO):
    id: str
    version: int
    type: str
    environment: Optional[str]
    params: Optional[List[str]]
    code: str
    input_specs: Optional[Dict]
    output_specs: Optional[Dict]
    config_specs: Optional[Dict]
    live_task: CommunityLiveTaskDTO


class CommunityCreateLiveTaskDTO(BaseModelDTO):
    title: str
    type: str
    space: Any


class CommunityLiveTaskVersionCreateResDTO(BaseModelDTO):
    id: str
    live_task_version: str
