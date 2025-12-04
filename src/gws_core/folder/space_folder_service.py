from typing import List, Type

from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.core.utils.logger import Logger
from gws_core.folder.model_with_folder import ModelWithFolder
from gws_core.note.note import Note
from gws_core.resource.resource_model import ResourceModel
from gws_core.scenario.scenario import Scenario
from gws_core.space.space_service import SpaceService

from .space_folder import SpaceFolder
from .space_folder_dto import ExternalSpaceFolder, ExternalSpaceFolders


class SpaceFolderService:
    entity_with_folders: List[Type[ModelWithFolder]] = [Scenario, Note, ResourceModel]

    @classmethod
    def get_folder_trees(cls) -> List[SpaceFolder]:
        return list(SpaceFolder.get_roots())

    @classmethod
    def synchronize_all_space_folders(cls) -> None:
        """
        Synchronize all the folders from space
        """

        Logger.info("Synchronizing folders from space")

        try:
            external_folders = SpaceService.get_instance().get_all_lab_root_folders()
            cls.synchronize_all_folders(external_folders)

            Logger.info(f"{len(external_folders.folders)} root folders synchronized from space")
        except Exception as err:
            Logger.error(f"Error while synchronizing folders from space: {err}")
            raise err

    @classmethod
    def synchronize_folder(cls, folder_id: str) -> None:
        """
        Synchronize a folder from space
        """
        space_root_folder = SpaceService.get_instance().get_lab_root_folder(folder_id)
        cls.synchronize_space_folder(space_root_folder)

    @classmethod
    def synchronize_all_folders(cls, external_folders: ExternalSpaceFolders) -> None:
        """Method that synchronize a list of folders from space into the lab"""

        for space_folder in external_folders.folders:
            # sync the root folder and its children but do not delete the children
            # as they might have moved, the deletetion is handled after
            cls._synchronize_space_folder(space_folder, None)

        # check the folders to delete
        current_root_folders: List[SpaceFolder] = list(SpaceFolder.get_roots())
        for root_folder in current_root_folders:
            cls._delete_folder_on_sync(root_folder, external_folders)

    @classmethod
    def _delete_folder_on_sync(
        cls, folder: SpaceFolder, external_folders: ExternalSpaceFolders
    ) -> None:
        """
        Method that loop through all folder children in DB and
        delete them if they are not in the external folders.
        It is used after synced to delete the folders that were removed from the space
        """
        if not external_folders.folder_exist(folder.id):
            cls.delete_folder(folder.id)

        for child in folder.children:
            cls._delete_folder_on_sync(child, external_folders)

    @classmethod
    def synchronize_space_folder(cls, external_folder: ExternalSpaceFolder) -> None:
        """Method that synchronize a folder from space into the lab"""

        cls._synchronize_space_folder(external_folder, None)

        # delete the children folder that were removed from the space folder
        root_folder = SpaceFolder.get_by_id_and_check(external_folder.id)
        if external_folder.children:
            folders = ExternalSpaceFolders(folders=[external_folder])
            cls._delete_folder_on_sync(root_folder, folders)

    @classmethod
    def _synchronize_space_folder(
        cls, external_folder: ExternalSpaceFolder, parent: ExternalSpaceFolder
    ) -> None:
        """Method that synchronize a folder from space into the lab"""

        lab_folder = SpaceFolder.get_by_id(external_folder.id)

        if lab_folder is None:
            lab_folder = SpaceFolder()
            lab_folder.id = external_folder.id

        # update other fields
        lab_folder.name = external_folder.name
        lab_folder.parent = parent
        lab_folder.save()

        if external_folder.children is not None:
            for child in external_folder.children:
                cls._synchronize_space_folder(child, lab_folder)

    @classmethod
    def delete_folder(cls, folder_id: str) -> None:
        """Method that delete a folder from the lab"""
        folder = SpaceFolder.get_by_id(folder_id)

        if folder is None:
            return

        folders = folder.get_with_children_as_list()

        # check if one of the sync scenario is attached to the folder
        if (
            Scenario.select()
            .where((Scenario.folder.in_(folders)) & (Scenario.validated_at.is_null(False)))
            .count()
            > 0
        ):
            raise BadRequestException(
                detail=GWSException.DELETE_FOLDER_WITH_SCENARIOS.value,
                unique_code=GWSException.DELETE_FOLDER_WITH_SCENARIOS.name,
            )

        # check if one of the note is attached to the folder
        if (
            Note.select()
            .where((Note.folder.in_(folders)) & (Note.validated_at.is_null(False)))
            .count()
            > 0
        ):
            raise BadRequestException(
                detail=GWSException.DELETE_FOLDER_WITH_NOTES.value,
                unique_code=GWSException.DELETE_FOLDER_WITH_NOTES.name,
            )

        # Clear all objects that are using the folder
        for entity in cls.entity_with_folders:
            entity.clear_folder(folders)

        folder.delete_instance()

    @classmethod
    def move_folder(cls, folder_id: str, new_parent_id: str) -> None:
        if folder_id == new_parent_id:
            raise BadRequestException("Cannot move a folder into itself")

        folder = SpaceFolder.get_by_id_and_check(folder_id)
        new_parent = SpaceFolder.get_by_id_and_check(new_parent_id)

        # check if the new parent is not a child of the folder
        if new_parent.has_ancestor(folder_id):
            raise BadRequestException("Cannot move a folder into a child folder")

        folder.parent = new_parent
        folder.save()

    @classmethod
    def get_by_id_and_check(cls, folder_id: str) -> SpaceFolder:
        return SpaceFolder.get_by_id_and_check(folder_id)
