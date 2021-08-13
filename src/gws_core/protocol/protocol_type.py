# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from json import dumps
from typing import Union

from peewee import ModelSelect

from ..model.typing import Typing, TypingObjectType


class ProtocolType(Typing):
    """
    ProtocolType class.
    """

    _object_type: TypingObjectType = "PROTOCOL"

    @classmethod
    def get_types(cls) -> ModelSelect:
        return cls.get_by_object_type(cls._object_type)

    def to_json(self, *, stringify: bool = False, prettify: bool = False, **kwargs) -> Union[str, dict]:

        _json = super().to_json(**kwargs)
        model_t = self.get_model_type(self.model_type)
        _json["data"]["graph"] = model_t.get_template().graph

        if stringify:
            if prettify:
                return dumps(_json, indent=4)
            else:
                return dumps(_json)
        else:
            return _json
