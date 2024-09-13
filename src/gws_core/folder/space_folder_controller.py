

from typing import List

from fastapi.param_functions import Depends

from gws_core.folder.space_folder_dto import SpaceFolderTreeDTO

from ..core_controller import core_app
from ..user.auth_service import AuthService
from .space_folder_service import SpaceFolderService


@core_app.post("/space-folder/synchronize", tags=["Folder"])
def synchronize_folder(_=Depends(AuthService.check_user_access_token)) -> None:
    """
    Synchronize the folders from space
    """

    SpaceFolderService.synchronize_all_space_folders()


@core_app.get("/space-folder/trees", tags=["Folder"])
def get_folder_trees(_=Depends(AuthService.check_user_access_token)) -> List[SpaceFolderTreeDTO]:
    """
    Get the list of available folders with children.
    """

    folders = SpaceFolderService.get_folder_trees()
    return [folder.to_tree_dto() for folder in folders]
