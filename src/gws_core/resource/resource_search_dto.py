

from typing import List, Optional

from gws_core.resource.resource_model import ResourceOrigin
from gws_core.tag.tag import Tag
from pydantic.main import BaseModel


class ResourceSearchDTO(BaseModel):

    tags: Optional[str]
    origin: Optional[ResourceOrigin]
    experiment_uri: Optional[str]
    task_uri: Optional[str]
    resource_typing_name: Optional[str]
    data: Optional[str]
