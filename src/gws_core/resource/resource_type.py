# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
from typing import Any, Dict, Type, final

from peewee import ModelSelect

from ..core.utils.utils import Utils
from ..model.typing import Typing, TypingObjectType
from ..resource.resource import Resource

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

    def to_json(self, deep: bool = False, **kwargs) -> dict:

        _json: Dict[str, Any] = super().to_json(**kwargs)

        # for compatibility
        _json["rtype"] = self.model_type

        return _json

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns a JSON string or dictionnary representation of the model.
        :return: The representation
        :rtype: `dict`, `str`
        """
        _json: Dict[str, Any] = super().data_to_json(**kwargs)

        # retrieve the process python type
        model_t: Type[Resource] = Utils.get_model_type(self.model_type)

        # TODO To fix
       # Other infos
        _json["title"] = model_t._human_name
        _json["description"] = model_t._short_description
        _json["doc"] = inspect.getdoc(model_t)

        return _json
