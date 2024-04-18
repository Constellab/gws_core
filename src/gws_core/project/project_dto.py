

from enum import Enum
from typing import List, Optional

from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO


class ProjectLevelStatus(Enum):
    PARENT = 'PARENT'
    LEAF = 'LEAF'


class SpaceProject(BaseModelDTO):

    id: str
    code: str
    title: str
    children: Optional[List['SpaceProject']] = None
    levelStatus: ProjectLevelStatus


class ProjectDTO(ModelDTO):
    code: str
    title: str
    levelStatus: ProjectLevelStatus


class ProjectTreeDTO(ProjectDTO):
    children: List['ProjectTreeDTO']
