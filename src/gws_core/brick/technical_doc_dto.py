# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.protocol.protocol_dto import ProtocolTypingFullDTO
from gws_core.resource.resource_typing_dto import ResourceTypingDTO
from gws_core.task.task_dto import TaskTypingDTO


class TechnicalDocDTO(BaseModelDTO):

    json_version: int
    brick_name: str
    brick_version: str
    resources: List[ResourceTypingDTO]
    tasks: List[TaskTypingDTO]
    protocols: List[ProtocolTypingFullDTO]
