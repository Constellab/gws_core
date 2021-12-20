
from typing import Any, TypedDict

from pydantic import BaseModel


class CentralProject(TypedDict):

    id: str
    title: str
    description: str


class ProjectDto(BaseModel):

    id: str = None
    title: str = None
    description: str = None

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ProjectDto):
            return False
        return self.id == other.id
