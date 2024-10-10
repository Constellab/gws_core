

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO


class NoteTemplateDTO(ModelWithUserDTO):
    title: str


class CreateNoteTemplateDTO(BaseModelDTO):
    title: str


class CreateNoteTemplateFromNoteDTO(BaseModelDTO):
    note_id: str
