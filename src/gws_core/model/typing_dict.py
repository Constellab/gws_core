# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from enum import Enum
from typing import Literal

from gws_core.core.model.model_dto import BaseModelDTO


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
