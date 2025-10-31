

from typing import Any, List, final

from gws_core.core.db.gws_core_db_manager import GwsCoreDbManager
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.core.utils.date_helper import DateHelper
from gws_core.entity_navigator.entity_navigator_type import (
    NavigableEntity, NavigableEntityType)
from gws_core.folder.model_with_folder import ModelWithFolder
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_field import RichTextField
from gws_core.impl.rich_text.rich_text_modification import \
    RichTextModificationsDTO
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.note.note_dto import NoteDTO, NoteFullDTO
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.user.current_user_service import CurrentUserService
from gws_core.user.user import User
from peewee import (BooleanField, CharField, CompositeKey, ForeignKeyField,
                    ModelSelect)

from ..core.model.base_model import BaseModel
from ..core.model.db_field import BaseDTOField, DateTimeUTC
from ..core.model.model_with_user import ModelWithUser
from ..folder.space_folder import SpaceFolder
from ..lab.lab_config_model import LabConfigModel
from ..scenario.scenario import Scenario


@final
class Note(ModelWithUser, ModelWithFolder, NavigableEntity):
    title = CharField()

    content: RichTextDTO = RichTextField(null=True)

    folder: SpaceFolder = ForeignKeyField(SpaceFolder, null=True)

    lab_config: LabConfigModel = ForeignKeyField(LabConfigModel, null=True)

    is_validated: bool = BooleanField(default=False)
    validated_at = DateTimeUTC(null=True)
    validated_by = ForeignKeyField(User, null=True, backref='+')

    # Date of the last synchronisation with space, null if never synchronised
    last_sync_at = DateTimeUTC(null=True)
    last_sync_by = ForeignKeyField(User, null=True, backref='+')

    is_archived = BooleanField(default=False, index=True)

    modifications: RichTextModificationsDTO = BaseDTOField(RichTextModificationsDTO, null=True)


    def get_content_as_rich_text(self) -> RichText:
        return RichText(self.content)

    def update_content_rich_text(self, rich_text: RichText) -> None:
        self.content = rich_text.to_dto()

    def check_is_updatable(self) -> None:
        """Throw an error if the note is not updatable
        """
        # check scenario status
        if self.is_validated:
            raise BadRequestException(GWSException.NOTE_VALIDATED.value, GWSException.NOTE_VALIDATED.name)
        if self.is_archived:
            raise BadRequestException(
                detail="The note is archived, please unachived it to update it")

    def to_dto(self) -> NoteDTO:
        return NoteDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            title=self.title,
            folder=self.folder.to_dto() if self.folder else None,
            is_validated=self.is_validated,
            validated_at=self.validated_at,
            validated_by=self.validated_by.to_dto() if self.validated_by else None,
            last_sync_at=self.last_sync_at,
            last_sync_by=self.last_sync_by.to_dto() if self.last_sync_by else None,
            is_archived=self.is_archived
        )

    def to_full_dto(self) -> NoteFullDTO:
        return NoteFullDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            title=self.title,
            folder=self.folder.to_dto() if self.folder else None,
            is_validated=self.is_validated,
            validated_at=self.validated_at,
            validated_by=self.validated_by.to_dto() if self.validated_by else None,
            last_sync_at=self.last_sync_at,
            last_sync_by=self.last_sync_by.to_dto() if self.last_sync_by else None,
            is_archived=self.is_archived,
            content=self.content,
            modifications=self.modifications
        )

    def validate(self) -> None:
        self.is_validated = True
        self.validated_at = DateHelper.now_utc()
        self.validated_by = CurrentUserService.get_and_check_current_user()
        self.lab_config = LabConfigModel.get_current_config()

    def archive(self, archive: bool) -> 'Note':

        if self.is_archived == archive:
            return self
        self.is_archived = archive
        return self.save()

    def get_navigable_entity_name(self) -> str:
        return self.title

    def get_navigable_entity_type(self) -> NavigableEntityType:
        return NavigableEntityType.NOTE

    def navigable_entity_is_validated(self) -> bool:
        return self.is_validated

    @GwsCoreDbManager.transaction()
    def delete_instance(self, *args, **kwargs) -> Any:
        result = super().delete_instance(*args, **kwargs)
        EntityTagList.delete_by_entity(TagEntityType.VIEW, self.id)
        return result

    @classmethod
    def get_synced_objects(cls) -> List['Note']:
        """Get all notes that are synced with space

        :return: [description]
        :rtype: [type]
        """
        return list(cls.select().where(cls.last_sync_at.is_null(False)))

    @classmethod
    def clear_folder(cls, folders: List[SpaceFolder]) -> None:
        cls.update(folder=None, last_sync_at=None, last_sync_by=None).where(cls.folder.in_(folders)).execute()

    class Meta:
        table_name = 'gws_note'
        is_table = True


class NoteScenario(BaseModel):
    """Many to Many relation between Note <-> Scenario

    :param BaseModel: [description]
    :type BaseModel: [type]
    :return: [description]
    :rtype: [type]
    """

    scenario = ForeignKeyField(Scenario, on_delete='CASCADE')
    note = ForeignKeyField(Note, on_delete='CASCADE')


    ############################################# CLASS METHODS ########################################

    @classmethod
    def create_obj(cls, scenario: Scenario, note: Note) -> 'NoteScenario':
        note_exp: 'NoteScenario' = NoteScenario()
        note_exp.scenario = scenario
        note_exp.note = note
        return note_exp

    @classmethod
    def delete_obj(cls, scenario_id: str, note_id: str) -> None:
        return cls.delete().where((cls.scenario == scenario_id) & (cls.note == note_id)).execute()

    @classmethod
    def find_by_pk(cls, scenario_id: str, note_id: str) -> ModelSelect:
        return cls.select().where((cls.scenario == scenario_id) & (cls.note == note_id))

    @classmethod
    def find_notes_by_scenarios(cls, scenario_id: List[str]) -> List[Note]:
        list_: List[NoteScenario] = list(cls.select().where(cls.scenario.in_(scenario_id)))

        return [x.note for x in list_]

    @classmethod
    def find_synced_notes_by_scenario(cls, scenario_id: str) -> List[Note]:
        list_: List[NoteScenario] = list(cls.select().where(
            (cls.scenario == scenario_id) & (cls.note.last_sync_at.is_null(False)))
            .join(Note)
        )

        return [x.note for x in list_]

    @classmethod
    def find_scenarios_by_note(cls, note_id: str) -> List[Scenario]:
        list_: List[NoteScenario] = list(cls.select().where(cls.note == note_id))

        return [x.scenario for x in list_]

    def save(self, *args, **kwargs) -> 'BaseModel':
        """Use force insert because it is a composite key
        https://stackoverflow.com/questions/30038185/python-peewee-save-doesnt-work-as-expected

        :return: [description]
        :rtype: [type]
        """
        return super().save(*args, force_insert=True, **kwargs)

    class Meta:
        table_name = 'gws_note_scenario'
        is_table = True
        primary_key = CompositeKey("scenario", "note")
