# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from __future__ import annotations

from typing import TYPE_CHECKING, List, Type

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.model.typing_dto import TypingObjectType

if TYPE_CHECKING:
    from gws_core.core.model.model import Model


class TypingNameObj():
    object_type: TypingObjectType
    brick_name: str
    unique_name: str

    SEPARATOR: str = "."

    def __init__(self, object_type: TypingObjectType, brick_name: str, unique_name: str) -> None:
        self.object_type = object_type
        self.brick_name = brick_name
        self.unique_name = unique_name

    def __str__(self) -> str:
        return TypingNameObj.typing_obj_to_str(self.object_type, self.brick_name, self.unique_name)

    def get_model_type(self) -> Type[Model]:
        # set import here to avoid circular import
        from gws_core.protocol.protocol_model import ProtocolModel
        from gws_core.resource.resource_model import ResourceModel
        from gws_core.task.task_model import TaskModel
        if self.object_type == 'TASK':
            return TaskModel
        elif self.object_type == 'PROTOCOL':
            return ProtocolModel
        elif self.object_type == 'RESOURCE':
            return ResourceModel
        else:
            raise BadRequestException(f"No model for type '{self.object_type}'")

    @staticmethod
    def from_typing_name(typing_name: str) -> 'TypingNameObj':
        try:
            parts: List[str] = typing_name.split(TypingNameObj.SEPARATOR)
            return TypingNameObj(object_type=parts[0], brick_name=parts[1], unique_name=parts[2])
        except:
            raise BadRequestException(f"The typing name '{typing_name}' is invalid")

    # Simple method to build the typing name  = object_type.brick.unique_name
    @staticmethod
    def typing_obj_to_str(object_type: str, brick_name: str, unique_name: str) -> str:
        return f"{object_type}{TypingNameObj.SEPARATOR}{brick_name}{TypingNameObj.SEPARATOR}{unique_name}"
