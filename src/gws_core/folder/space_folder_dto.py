from typing import List, Optional

from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO


class ExternalSpaceFolder(BaseModelDTO):
    """Format of folder send by space API
    """
    id: str
    title: str
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
    title: str


class SpaceFolderTreeDTO(SpaceFolderDTO):
    children: List['SpaceFolderTreeDTO']
