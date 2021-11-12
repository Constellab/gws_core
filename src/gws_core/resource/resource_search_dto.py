

from typing import List

from gws_core.tag.tag import Tag
from pydantic.main import BaseModel


class ResourceSearchDTO(BaseModel):

    tags: List[Tag]
