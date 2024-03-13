

from datetime import datetime
from typing import Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.project.project_dto import ProjectDTO
from gws_core.user.user_dto import UserDTO


class ReportSaveDTO(BaseModelDTO):
    title: str = None
    project_id: Optional[str] = None
    template_id: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True


class ReportDTO(ModelWithUserDTO):
    title: str
    project: Optional[ProjectDTO]
    is_validated: bool
    validated_at: Optional[datetime]
    validated_by: Optional[UserDTO]
    last_sync_at: Optional[datetime]
    last_sync_by: Optional[UserDTO]
    is_archived: bool


class ReportFullDTO(ReportDTO):
    content: RichTextDTO
