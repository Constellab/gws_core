# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, List, TypedDict

from pydantic import BaseModel


class CentralProject(TypedDict):

    id: str
    code: str
    title: str
    children: List['CentralProject']


class ProjectDto(BaseModel):

    id: str = None
    title: str = None

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, ProjectDto):
            return False
        return self.id == other.id
