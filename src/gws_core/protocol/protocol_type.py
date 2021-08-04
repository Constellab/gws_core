# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from json import dumps
from typing import Union

from ..model.typing import Typing


class ProtocolType(Typing):
    """
    ProtocolType class.
    """

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
