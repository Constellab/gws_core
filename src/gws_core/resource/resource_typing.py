# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List, Type

from peewee import ModelSelect

from ..impl.file.file import File
from ..model.typing import Typing, TypingObjectType

# ####################################################################
#
# ResourceType class
#
# ####################################################################


class ResourceTyping(Typing):
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

        if not deep:
            return None

        _json = super().data_to_json(deep=deep, **kwargs)

        # Other infos
        _json["doc"] = self.get_model_type_doc()

        return _json


class FileTyping(ResourceTyping):

    @classmethod
    def get_typings(cls) -> List['ResourceTyping']:
        return cls.get_children_typings(cls._object_type, File)

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        _json = super().to_json(deep, **kwargs)

        file_type: Type[File] = self.get_type()

        # Add the list of default extensions for the file
        _json["supported_extensions"] = file_type.supported_extensions

        return _json
