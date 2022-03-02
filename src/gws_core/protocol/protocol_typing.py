# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, Dict, Literal, Type, final

from peewee import CharField, ModelSelect

from ..model.typing import Typing, TypingObjectType
from ..process.process_factory import ProcessFactory
from ..protocol.protocol import Protocol
from ..protocol.protocol_model import ProtocolModel

ProtocolSubType = Literal["PROTOCOL"]


@final
class ProtocolTyping(Typing):
    """
    ProtocolType class.
    """

    # Sub type of the object, types will be differents based on object type
    object_sub_type: ProtocolSubType = CharField(null=True, max_length=20)

    _object_type: TypingObjectType = "PROTOCOL"

    @classmethod
    def get_types(cls) -> ModelSelect:
        return cls.get_by_object_type(cls._object_type)

    def model_type_to_json(self, model_t: Type[Protocol]) -> dict:
        protocol: ProtocolModel = ProcessFactory.create_protocol_model_from_type(
            model_t)
        return {
            "graph": protocol.dumps_data(minimize=False),
            "doc": self.get_model_type_doc(),
        }
