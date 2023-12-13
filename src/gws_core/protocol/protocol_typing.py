# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Literal, Type, final

from peewee import CharField, ModelSelect

from gws_core.core.utils.date_helper import DateHelper
from gws_core.protocol.protocol_dto import ProtocolTypingFullDTO

from ..model.typing import Typing
from ..model.typing_dict import TypingObjectType
from ..protocol.protocol import Protocol

ProtocolSubType = Literal["PROTOCOL", "MANUAL_PROTOCOL"]


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

    @classmethod
    def new_manual_protocol(cls, graph: dict,
                            human_name: str, short_description: str = None) -> 'ProtocolTyping':

        # retrieve the protocol typing to copy info from it
        protocol_typing: Typing = Typing.get_by_object_type(Protocol)

        typing = ProtocolTyping(
            model_type=protocol_typing.model_type,
            brick=protocol_typing.brick,
            brick_version=protocol_typing.brick_version,
            unique_name=str(DateHelper.now_utc_as_milliseconds()),
            object_type=cls._object_type,
            human_name=human_name,
            short_description=short_description,
            hide=False,
            object_sub_type="MANUAL_PROTOCOL",
        )

        typing.data['graph'] = graph
        return typing

    def to_full_dto(self) -> ProtocolTypingFullDTO:
        typing_dto = super().to_full_dto()

        protocol_typing = ProtocolTypingFullDTO(
            **typing_dto.dict(),
        )

        # retrieve the task python type
        model_t: Type[Protocol] = self.get_type()

        if self.object_sub_type == "PROTOCOL" and model_t:
            protocol: Protocol = model_t.instantiate_protocol()
            # json_["graph"] = protocol.dumps_data(minimize=False)
            protocol_typing.input_specs = protocol.get_input_specs_self().to_dto()
            protocol_typing.output_specs = protocol.get_output_specs_self().to_dto()
            protocol_typing.config_specs = {}

        return protocol_typing
