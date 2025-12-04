from datetime import datetime
from typing import Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.folder.space_folder_dto import SpaceFolderDTO
from gws_core.impl.rich_text.rich_text_modification import RichTextModificationsDTO
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.user.user_dto import UserDTO


class NoteSaveDTO(BaseModelDTO):
    title: str = None
    folder_id: Optional[str] = None
    template_id: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class NoteDTO(ModelWithUserDTO):
    title: str
    folder: Optional[SpaceFolderDTO]
    is_validated: bool
    validated_at: Optional[datetime]
    validated_by: Optional[UserDTO]
    last_sync_at: Optional[datetime]
    last_sync_by: Optional[UserDTO]
    is_archived: bool


class NoteFullDTO(NoteDTO):
    content: RichTextDTO
    modifications: Optional[RichTextModificationsDTO]


class NoteInsertTemplateDTO(BaseModelDTO):
    block_index: int
    note_template_id: str
