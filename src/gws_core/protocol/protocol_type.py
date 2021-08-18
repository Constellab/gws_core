# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Type, final

from peewee import ModelSelect

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

        model_t: Type[Protocol] = self.get_model_type(self.model_type)
        _json["graph"] = model_t.get_template().graph  # todo fix method

        return _json
