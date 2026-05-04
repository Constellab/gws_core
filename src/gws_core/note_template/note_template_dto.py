from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO


class NoteTemplateDTO(ModelWithUserDTO):
    title: str


class CreateNoteTemplateDTO(BaseModelDTO):
    title: str


class CreateNoteTemplateFromNoteDTO(BaseModelDTO):
    note_id: str


class InsertFormTemplateBlockDTO(BaseModelDTO):
    """Insert a FORM_TEMPLATE block in a NoteTemplate, referencing a PUBLISHED
    FormTemplateVersion. ``form_template_id`` is derived from the version
    server-side; clients provide only the version id.
    """

    form_template_version_id: str
    position: int | None = None
    display_name: str | None = None
