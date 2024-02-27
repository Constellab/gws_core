# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from gws_core.core.model.model_dto import ModelDTO
from gws_core.model.typing_dict import TypingRefDTO, TypingStatus


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
    icon: Optional[str]


class TypingFullDTO(TypingDTO):
    parent: Optional[TypingRefDTO] = None
    doc: Optional[str] = None
