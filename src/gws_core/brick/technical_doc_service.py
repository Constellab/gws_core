# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Type

from gws_core.brick.technical_doc_dto import TechnicalDocDTO
from gws_core.model.typing_dto import TypingFullDTO
from gws_core.protocol.protocol_typing import ProtocolTyping

from ..model.typing import Typing
from ..resource.resource import Resource
from ..resource.resource_typing import ResourceTyping
from ..task.task_typing import TaskTyping
from .brick_helper import BrickHelper


class TechnicalDocService():

    @classmethod
    def generate_technical_doc(cls, brick_name: str) -> TechnicalDocDTO:
        """Method to return the technical doc information about a brick to upload it on the hub
        """

        brick_info = BrickHelper.get_brick_info_and_check(brick_name)

        return TechnicalDocDTO(
            json_version=1,
            brick_name=brick_info["name"],
            brick_version=brick_info["version"],
            resources=cls.export_typing_technical_doc(brick_name, ResourceTyping),
            tasks=cls.export_typing_technical_doc(brick_name, TaskTyping),
            protocols=cls.export_typing_technical_doc(brick_name, ProtocolTyping),
        )

    @classmethod
    def export_typing_technical_doc(cls, brick_name: str, typing_class: Type[Typing]) -> list:
        typings: List[Typing] = typing_class.get_by_brick_and_object_type(brick_name)
        sorted_typings = sorted(typings, key=lambda x: len(x.get_ancestors()))
        json_list = []
        for typing in sorted_typings:
            json_ = cls._get_typing_technical_doc(typing)

            if json_ is None:
                continue

            json_list.append(json_)
        return json_list

    @classmethod
    def _get_typing_technical_doc(cls, typing: Typing) -> TypingFullDTO:
        type_: Type[Resource] = typing.get_type()
        if type_ is None:
            return None
        return typing.to_full_dto()
