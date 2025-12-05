from typing import Literal

from gws_core.core.utils.logger import Logger
from gws_core.folder.space_folder import SpaceFolder
from gws_core.note.note import Note
from gws_core.scenario.scenario import Scenario
from gws_core.space.space_dto import SpaceSyncObjectDTO
from gws_core.space.space_service import SpaceService
from gws_core.user.user import User


class SpaceObjectService:
    """Service to manage sync from space to lab"""

    @classmethod
    def sync_scenarios_from_space(cls) -> None:
        space_scenarios = SpaceService.get_instance().get_synced_scenarios()

        cls._sync_objects_from_space(space_scenarios, Scenario, "scenario")

    @classmethod
    def sync_scenario_from_space(cls, scenario: SpaceSyncObjectDTO) -> None:
        cls._sync_object_from_space(scenario, Scenario)

    @classmethod
    def sync_notes_from_space(cls) -> None:
        space_notes = SpaceService.get_instance().get_synced_notes()

        cls._sync_objects_from_space(space_notes, Note, "note")

    @classmethod
    def sync_note_from_space(cls, note: SpaceSyncObjectDTO) -> None:
        cls._sync_object_from_space(note, Note)

    @classmethod
    def _sync_objects_from_space(
        cls,
        space_objects: list[SpaceSyncObjectDTO],
        object_model: type[Note] | type[Scenario],
        object_type: Literal["note", "scenario"],
    ) -> None:
        Logger.info(f"Syncing {object_type} from space")

        for space_object in space_objects:
            cls._sync_object_from_space(space_object, object_model)

        # check unsynced notes
        space_object_ids = [obj.id for obj in space_objects]
        lab_objects = object_model.get_synced_objects()
        for lab_object in lab_objects:
            if lab_object.id not in space_object_ids:
                lab_object.last_sync_at = None
                lab_object.last_sync_by = None
                lab_object.save(skip_hook=True)
                Logger.info(f"{object_type} {lab_object.id} unsynced from space")

        Logger.info(f"{len(space_objects)} {object_type} synchronized from space")

    @classmethod
    def _sync_object_from_space(
        cls, space_object: SpaceSyncObjectDTO, object_model: type[Note] | type[Scenario]
    ) -> None:
        try:
            lab_note = object_model.get_by_id(space_object.id)
            if lab_note is not None and (
                lab_note.folder is None or lab_note.folder.id != space_object.folder_id
            ):
                folder = SpaceFolder.get_by_id(space_object.folder_id)

                if folder:
                    lab_note.folder = folder
                    lab_note.last_sync_at = space_object.last_sync_at

                    user = User.get_by_id(space_object.last_sync_by_id)
                    if user is None:
                        user = User.get_and_check_sysuser()
                    lab_note.last_sync_by = user
                    lab_note.save(skip_hook=True)
                    Logger.info(f"Note {space_object.id} moved to folder {folder.id}")

        except Exception as err:
            Logger.error(f"Error while syncing note {space_object.id} from space: {err}")
