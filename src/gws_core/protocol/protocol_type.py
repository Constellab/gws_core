# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from operator import mod
from typing import Type, final

from peewee import ModelSelect
from gws_core.process.processable_factory import ProcessableFactory

from gws_core.protocol.protocol_model import ProtocolModel

from ..model.typing import Typing, TypingObjectType
from ..protocol.protocol import Protocol


@final
class ProtocolType(Typing):
    """
    ProtocolType class.
    """

    _object_type: TypingObjectType = "PROTOCOL"

    @classmethod
    def get_types(cls) -> ModelSelect:
        return cls.get_by_object_type(cls._object_type)

    def data_to_json(self, shallow=False, bare: bool = False, **kwargs) -> dict:
        """
        Returns a JSON string or dictionnary representation of the model data.
        :return: The representation
        :rtype: `dict`
        """
        _json = super().data_to_json(**kwargs)

        protocol_type: Type[Protocol] = self.get_model_type(self.model_type)

        protocol: ProtocolModel = ProcessableFactory.create_protocol_from_type(
            protocol_type)
        _json["graph"] = protocol.dumps()

        return _json
