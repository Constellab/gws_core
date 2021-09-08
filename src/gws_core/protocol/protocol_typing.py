# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Type, final

from peewee import ModelSelect

from ..core.utils.utils import Utils
from ..model.typing import Typing, TypingObjectType
from ..processable.processable_factory import ProcessableFactory
from ..protocol.protocol import Protocol
from ..protocol.protocol_model import ProtocolModel


@final
class ProtocolTyping(Typing):
    """
    ProtocolType class.
    """

    _object_type: TypingObjectType = "PROTOCOL"

    @classmethod
    def get_types(cls) -> ModelSelect:
        return cls.get_by_object_type(cls._object_type)

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns a JSON string or dictionnary representation of the model data.
        :return: The representation
        :rtype: `dict`
        """

        if not deep:
            return None

        _json = super().data_to_json(deep=deep, **kwargs)

        protocol_type: Type[Protocol] = Utils.get_model_type(self.model_type)

        protocol: ProtocolModel = ProcessableFactory.create_protocol_model_from_type(
            protocol_type)
        _json["graph"] = protocol.dumps_data(minimize=False)

        # Other infos
        _json["doc"] = self.get_model_type_doc()

        return _json
