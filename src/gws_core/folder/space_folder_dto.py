from typing import List, Optional

from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO


class ExternalSpaceFolder(BaseModelDTO):
    """Format of folder send by space API
    """
    id: str
    title: str
    children: Optional[List['ExternalSpaceFolder']] = None


class SpaceFolderDTO(ModelDTO):
    title: str


class SpaceFolderTreeDTO(SpaceFolderDTO):
    children: List['SpaceFolderTreeDTO']
