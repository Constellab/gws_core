# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel

from gws_core.core.model.model_dto import ModelDTO


class ProjectLevelStatus(Enum):
    PARENT = 'PARENT'
    LEAF = 'LEAF'


class SpaceProject(BaseModel):

    id: str
    code: str
    title: str
    children: Optional[List['SpaceProject']]
    levelStatus: ProjectLevelStatus


class ProjectDTO(ModelDTO):
    code: str
    title: str
    levelStatus: ProjectLevelStatus


class ProjectTreeDTO(ProjectDTO):
    children: List['ProjectTreeDTO']
