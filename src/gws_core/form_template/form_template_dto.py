from datetime import datetime
from enum import Enum

from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.user.user_dto import UserDTO


class FormTemplateVersionStatus(Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class FormTemplateDTO(ModelWithUserDTO):
    name: str
    description: str | None
    is_archived: bool


class FormTemplateVersionDTO(ModelWithUserDTO):
    template_id: str
    version: int
    status: FormTemplateVersionStatus
    content: dict | None
    published_at: datetime | None
    published_by: UserDTO | None


class FormTemplateFullDTO(FormTemplateDTO):
    """FormTemplate plus the list of its versions (summary)."""

    versions: list[FormTemplateVersionDTO]
