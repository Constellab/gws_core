from typing import List

from gws_core.core.model.base_model import BaseModel
from gws_core.resource.view_config.view_config import ViewConfig
from peewee import CompositeKey, ForeignKeyField, ModelSelect

from .note import Note


class NoteViewModel(BaseModel):
    """Model to store which views are used in notes"""

    note: Note = ForeignKeyField(Note, null=False, index=True, on_delete="CASCADE")
    view: ViewConfig = ForeignKeyField(ViewConfig, null=False, index=True, on_delete="RESTRICT")

    @classmethod
    def get_by_note(cls, note_id: str) -> List["NoteViewModel"]:
        return list(NoteViewModel.select().where(NoteViewModel.note == note_id))

    @classmethod
    def get_by_notes(cls, note_ids: List[str]) -> ModelSelect:
        return NoteViewModel.select().where(NoteViewModel.note.in_(note_ids))

    @classmethod
    def get_by_view(cls, view_config_id: str) -> ModelSelect:
        return NoteViewModel.select().where(NoteViewModel.view == view_config_id)

    @classmethod
    def get_by_views(cls, view_config_ids: List[str]) -> ModelSelect:
        return NoteViewModel.select().where(NoteViewModel.view.in_(view_config_ids))

    @classmethod
    def get_by_resource(cls, resource_id: str) -> ModelSelect:
        return (
            NoteViewModel.select()
            .join(ViewConfig, on=(NoteViewModel.view == ViewConfig.id))
            .join(Note, on=(NoteViewModel.note == Note.id))
            .where(NoteViewModel.view.resource_model == resource_id)
            .order_by(NoteViewModel.note.last_modified_at.desc())
        )

    @classmethod
    def get_by_resources(cls, resource_ids: List[str]) -> ModelSelect:
        return (
            NoteViewModel.select()
            .join(ViewConfig, on=(NoteViewModel.view == ViewConfig.id))
            .join(Note, on=(NoteViewModel.note == Note.id))
            .where(NoteViewModel.view.resource_model.in_(resource_ids))
            .order_by(NoteViewModel.note.last_modified_at.desc())
        )

    def save(self, *args, **kwargs) -> "BaseModel":
        """Use force insert because it is a composite key
        https://stackoverflow.com/questions/30038185/python-peewee-save-doesnt-work-as-expected

        :return: [description]
        :rtype: [type]
        """
        return super().save(*args, force_insert=True, **kwargs)

    class Meta:
        table_name = "gws_note_view"
        is_table = True
        primary_key = CompositeKey("note", "view")
