

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO


class DocumentTemplateDTO(ModelWithUserDTO):
    title: str


class CreateDocumentTemplateDTO(BaseModelDTO):
    title: str


class CreateDocumentTemplateFromNoteDTO(BaseModelDTO):
    note_id: str
