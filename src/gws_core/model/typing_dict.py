# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from enum import Enum
from typing import Literal, Optional, TypedDict


class TypingStatus(Enum):
    OK = 'OK'
    UNAVAILABLE = 'UNAVAILABLE'


# different object typed store in the typing table
TypingObjectType = Literal["TASK", "RESOURCE", "PROTOCOL", "MODEL"]


# Minimum object to reference another type
class TypingRef(TypedDict):
    typing_name: str
    brick_version: str
    human_name: str


class TypingDict(TypedDict):
    unique_name: str
    typing_name: str
    object_type: TypingObjectType
    object_sub_type: str
    human_name: str
    short_description: str
    deprecated_since: str
    deprecated_message: str
    status: TypingStatus
    hide: bool
    # only provided on deep dict
    doc: Optional[str]
    parent: TypingRef
