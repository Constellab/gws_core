

from enum import Enum
from typing import Literal, Optional

from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO
from gws_core.model.typing_style import TypingStyle


class TypingStatus(Enum):
    OK = 'OK'
    UNAVAILABLE = 'UNAVAILABLE'


# different object typed store in the typing table
TypingObjectType = Literal["TASK", "RESOURCE", "PROTOCOL", "MODEL", "ACTION", "APP"]


# Minimum object to reference another type
class TypingRefDTO(BaseModelDTO):
    typing_name: str
    brick_version: str
    human_name: str
    style: Optional[TypingStyle] = None
    short_description: Optional[str] = None


class TypingDTO(ModelDTO):
    unique_name: str
    object_type: str
    typing_name: str
    brick_version: str
    human_name: str
    short_description: Optional[str]
    object_sub_type: Optional[str]
    deprecated_since: Optional[str]
    deprecated_message: Optional[str]
    additional_data: Optional[dict]
    status: TypingStatus
    hide: bool
    style: Optional[TypingStyle]


class TypingFullDTO(TypingDTO):
    parent: Optional[TypingRefDTO] = None
    doc: Optional[str] = None

    def to_markdown(self) -> str:
        markdown = f'## {self.human_name}\n\n'

        markdown += f'Typing name: {self.typing_name}.'

        if self.short_description:
            markdown += f' Short description: {self.short_description}.'

        if self.deprecated_since and self.deprecated_message:
            markdown += f' Deprecated since: {self.deprecated_since}. Reason: {self.deprecated_message}.'

        if self.hide:
            markdown += ' This task is hidden from playground.'

        if self.parent:
            markdown += f' Parent class: {self.parent.typing_name}.'

        if self.doc:
            # replace titles
            doc = self.doc.replace('\n# ', '\n### ').replace('\n## ', '\n### ')
            markdown += f'{doc}'

        return markdown


class SimpleTypingDTO(BaseModelDTO):
    human_name: str = None
    short_description: Optional[str] = None
