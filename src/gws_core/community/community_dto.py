from gws_core.core.model.model_dto import BaseModelDTO
from typing import Dict, Optional

class CommunityLiveTaskDTO(BaseModelDTO):
    id: str
    title: str

class CommunityLiveTaskVersionDTO(BaseModelDTO):
    id: str
    version: int
    type: str
    environment: Optional[str]
    code: str
    input_specs: Dict
    output_specs: Dict
    config_specs: Dict
    live_task: CommunityLiveTaskDTO