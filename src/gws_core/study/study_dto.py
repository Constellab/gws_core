
from typing import Any, TypedDict

from pydantic import BaseModel


class CentralStudy(TypedDict):

    id: str
    title: str
    description: str


class StudyDto(BaseModel):

    id: str = None
    title: str = None
    description: str = None

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, StudyDto):
            return False
        return self.id == other.id
