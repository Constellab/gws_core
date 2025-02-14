from datetime import datetime
from typing import List, Optional

from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO
from gws_core.tag.tag import Tag
from gws_core.tag.tag_dto import TagDTO


class ExternalSpaceFolder(BaseModelDTO):
    """Format of folder send by space API
    """
    id: str
    name: str
    children: Optional[List['ExternalSpaceFolder']] = None

    def folder_exist(self, folder_id: str) -> bool:
        """Check if a folder exist in the tree
        """
        if self.id == folder_id:
            return True

        if self.children is None:
            return False

        for child in self.children:
            if child.folder_exist(folder_id):
                return True

        return False


class ExternalSpaceFolders(BaseModelDTO):
    folders: List[ExternalSpaceFolder]

    def folder_exist(self, folder_id: str) -> bool:
        """Check if a folder exist in the tree
        """
        for root_folder in self.folders:
            if root_folder.folder_exist(folder_id):
                return True

        return False


class SpaceFolderDTO(ModelDTO):
    name: str


class SpaceFolderTreeDTO(SpaceFolderDTO):
    children: List['SpaceFolderTreeDTO']


class ExternalSpaceCreateFolderDTO(BaseModelDTO):
    name: str
    code: Optional[str] = None
    tags: Optional[List[TagDTO]] = None
    starting_date: Optional[datetime] = None
    ending_date: Optional[datetime] = None


class ExternalSpaceCreateFolder():
    name: str
    code: str
    tags: List[Tag] = None
    starting_date: Optional[datetime] = None
    ending_date: Optional[datetime] = None

    def __init__(self, name: str, code: str = None,
                 tags: List[Tag] = None,
                 starting_date: Optional[datetime] = None,
                 ending_date: Optional[datetime] = None):
        self.name = name
        self.code = code
        self.tags = tags or []
        self.starting_date = starting_date
        self.ending_date = ending_date

    def to_dto(self) -> ExternalSpaceCreateFolderDTO:
        return ExternalSpaceCreateFolderDTO(
            name=self.name,
            code=self.code,
            tags=[tag.to_dto() for tag in self.tags or []],
            starting_date=self.starting_date,
            ending_date=self.ending_date,
        )
