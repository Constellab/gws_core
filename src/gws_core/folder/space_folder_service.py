

from typing import List, Type

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.core.utils.logger import Logger
from gws_core.experiment.experiment import Experiment
from gws_core.folder.model_with_folder import ModelWithFolder
from gws_core.note.note import Note
from gws_core.resource.resource_model import ResourceModel
from gws_core.space.space_service import SpaceService

from .space_folder import SpaceFolder
from .space_folder_dto import ExternalSpaceFolder


class SpaceFolderService():

    entity_with_folders: List[Type[ModelWithFolder]] = [Experiment, Note, ResourceModel]

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
            external_folders = SpaceService.get_all_lab_folders()
            cls.synchronize_folders(external_folders)

            Logger.info(f"{len(external_folders)} folders synchronized from space")
        except Exception as err:
            Logger.error(f"Error while synchronizing folders from space: {err}")
            raise err

    @classmethod
    def synchronize_folder(cls, folder_id: str) -> None:
        """
        Synchronize a folder from space
        """
        space_root_folder = SpaceService.get_lab_root_folder(folder_id)
        cls.synchronize_space_folder(space_root_folder)

    @classmethod
    def synchronize_folders(cls, external_folders: List[ExternalSpaceFolder]) -> None:
        """Method that synchronize a list of folders from space into the lab
        """

        for space_folder in external_folders:
            cls.synchronize_space_folder(space_folder)

        # check the root folders to delete
        root_folders: List[SpaceFolder] = list(SpaceFolder.get_roots())
        external_folder_ids = [space_folder.id for space_folder in external_folders]
        for root_folder in root_folders:
            if root_folder.id not in external_folder_ids:
                cls.delete_folder(root_folder.id)

    @classmethod
    def synchronize_space_folder(cls, external_folder: ExternalSpaceFolder) -> None:
        """Method that synchronize a folder from space into the lab
        """

        cls._synchronize_space_folder(external_folder, None)

    @classmethod
    def _synchronize_space_folder(cls, external_folder: ExternalSpaceFolder, parent: ExternalSpaceFolder) -> None:
        """Method that synchronize a folder from space into the lab
        """

        lab_folder = SpaceFolder.get_by_id(external_folder.id)

        if lab_folder is None:
            lab_folder = SpaceFolder()
            lab_folder.id = external_folder.id

        # update other fields
        lab_folder.title = external_folder.title
        lab_folder.parent = parent
        lab_folder.save()

        # delete children that are not in the space folder
        if lab_folder.children:
            for child in lab_folder.children:
                if child.id not in [otherChild.id for otherChild in external_folder.children]:
                    cls.delete_folder(child.id)

        if external_folder.children is not None:
            for child in external_folder.children:
                cls._synchronize_space_folder(child, lab_folder)

    @classmethod
    def delete_folder(cls, folder_id: str) -> None:
        """Method that delete a folder from the lab
        """
        folder = SpaceFolder.get_by_id(folder_id)

        if folder is None:
            return

        folders = folder.get_with_children_as_list()

        # check if one of the sync experiment is attached to the folder
        if Experiment.select().where((Experiment.folder.in_(folders)) & (Experiment.last_sync_at.is_null(False))).count() > 0:
            raise BadRequestException(detail=GWSException.DELETE_FOLDER_WITH_EXPERIMENTS.value,
                                      unique_code=GWSException.DELETE_FOLDER_WITH_EXPERIMENTS.name)

        # check if one of the note is attached to the folder
        if Note.select().where((Note.folder.in_(folders)) & (Note.last_sync_at.is_null(False))).count() > 0:
            raise BadRequestException(detail=GWSException.DELETE_FOLDER_WITH_NOTES.value,
                                      unique_code=GWSException.DELETE_FOLDER_WITH_NOTES.name)

        # Clear all objects that are using the folder
        for entity in cls.entity_with_folders:
            entity.clear_folder(folders)

        folder.delete_instance()
        return None
