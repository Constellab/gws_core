# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from enum import Enum
from typing import Literal, Optional

from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO
from gws_core.model.typing_style import TypingStyle


class TypingStatus(Enum):
    OK = 'OK'
    UNAVAILABLE = 'UNAVAILABLE'


# different object typed store in the typing table
TypingObjectType = Literal["TASK", "RESOURCE", "PROTOCOL", "MODEL", "ACTION"]


# Minimum object to reference another type
class TypingRefDTO(BaseModelDTO):
    typing_name: str
    brick_version: str
    human_name: str
    style: Optional[TypingStyle] = None


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


class SimpleTypingDTO(BaseModelDTO):
    human_name: str = None
    short_description: Optional[str] = None
    style: Optional[TypingStyle] = None
