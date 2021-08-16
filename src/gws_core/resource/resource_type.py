# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
import json
from typing import Any, Dict, Type, Union, final

from gws_core.resource.resource import Resource
from peewee import ModelSelect

from ..model.typing import Typing, TypingObjectType

# ####################################################################
#
# ResourceType class
#
# ####################################################################


@final
class ResourceType(Typing):
    """
    ResourceType class.
    """

    _object_type: TypingObjectType = "RESOURCE"

    @classmethod
    def get_types(cls) -> ModelSelect:
        return cls.get_by_object_type(cls._object_type)

    def to_json(self, shallow=False, bare: bool = False, **kwargs) -> dict:

        _json: Dict[str, Any] = super().to_json(**kwargs)

        # for compatibility
        _json["rtype"] = self.model_type

        return _json

    def data_to_json(self, shallow=False, bare: bool = False, **kwargs) -> dict:
        """
        Returns a JSON string or dictionnary representation of the model.
        :return: The representation
        :rtype: `dict`, `str`
        """
        _json: Dict[str, Any] = super().data_to_json(**kwargs)

        # retrieve the process python type
        model_t: Type[Resource] = self.get_model_type(self.model_type)

       # Other infos
        _json["title"] = model_t.title
        _json["description"] = model_t.description
        _json["doc"] = inspect.getdoc(model_t)

        return _json
