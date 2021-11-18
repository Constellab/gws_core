

from typing import List, Optional

from gws_core.resource.resource_model import ResourceOrigin
from gws_core.tag.tag import Tag
from pydantic.main import BaseModel


class ResourceSearchDTO(BaseModel):

    tags: Optional[str]
    origin: Optional[ResourceOrigin]
    experiment_id: Optional[str]
    task_id: Optional[str]
    resource_typing_name: Optional[str]
    data: Optional[str]
