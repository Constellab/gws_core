
from fastapi.param_functions import Depends

from gws_core.folder.space_folder_dto import SpaceFolderDTO, SpaceFolderTreeDTO

from ..core_controller import core_app
from ..user.authorization_service import AuthorizationService
from .space_folder_service import SpaceFolderService


@core_app.post("/space-folder/synchronize", tags=["Folder"])
def synchronize_folder(_=Depends(AuthorizationService.check_user_access_token)) -> None:
    """
    Synchronize the folders from space
    """

    SpaceFolderService.synchronize_all_space_folders()


@core_app.get("/space-folder/trees", tags=["Folder"])
def get_folder_trees(
    _=Depends(AuthorizationService.check_user_access_token_or_app),
) -> list[SpaceFolderTreeDTO]:
    """
    Get the list of available folders with children.
    """

    folders = SpaceFolderService.get_folder_trees()
    return [folder.to_tree_dto() for folder in folders]


@core_app.get("/space-folder/{id_}", tags=["Folder"])
def get_folder(id_: str, _=Depends(AuthorizationService.check_user_access_token)) -> SpaceFolderDTO:
    """
    Get the folder with the given id.
    """

    return SpaceFolderService.get_by_id_and_check(id_).to_dto()
