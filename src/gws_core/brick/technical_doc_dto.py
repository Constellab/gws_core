# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.model.typing_dto import TypingFullDTO
from gws_core.protocol.protocol_dto import ProtocolTypingFullDTO
from gws_core.task.task_dto import TaskTypingDTO


class ResourceMethodDocDTO(BaseModelDTO):
    funcs: Optional[list]
    views: Optional[list]


class ResourceDocDTO(TypingFullDTO):
    methods: ResourceMethodDocDTO


class TechnicalDocDTO(BaseModelDTO):

    json_version: int
    brick_name: str
    brick_version: str
    resources: List[TypingFullDTO]
    tasks: List[TaskTypingDTO]
    protocols: List[ProtocolTypingFullDTO]
