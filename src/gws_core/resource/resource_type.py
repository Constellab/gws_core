# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
import json
from typing import Union

from ..model.typing import Typing

# ####################################################################
#
# ResourceType class
#
# ####################################################################


class ResourceType(Typing):
    """
    ResourceType class.
    """

    #rtype = CharField(null=True, index=True, unique=True)
    #base_rtype = CharField(null=True, index=True)
    #_table_name = 'gws_resource_type'

    # -- PROPERTIES --

    @property
    def rtype(self):
        return self.model_type

    @property
    def base_rtype(self):
        return self.root_model_type

    def to_json(self, *, stringify: bool = False, prettify: bool = False, **kwargs) -> Union[str, dict]:

        _json = super().to_json(**kwargs)

        # for compatibility
        _json["rtype"] = self.rtype
        _json["base_rtype"] = self.base_rtype

        model_t = self.get_model_type(self.model_type)

        if not _json.get("data"):
            _json["data"] = {}

        _json["data"]["title"] = model_t.title
        _json["data"]["description"] = model_t.description
        _json["data"]["doc"] = inspect.getdoc(model_t)

        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json