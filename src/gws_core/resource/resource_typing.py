# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Literal, Type

from peewee import ModelSelect

from ..model.typing import Typing, TypingObjectType

if TYPE_CHECKING:
    from ..impl.file.file import File


# Sub type of resource type
# RESOURCE --> normal resource
ResourceSubType = Literal["RESOURCE"]


class ResourceTyping(Typing):
    """
    ResourceType class.
    """

    _object_type: TypingObjectType = "RESOURCE"

    @classmethod
    def get_types(cls) -> ModelSelect:
        return cls.get_by_object_type(cls._object_type)

    @classmethod
    def get_folder_types(cls) -> List['ResourceTyping']:
        from ..impl.file.folder import Folder

        return cls.get_children_typings(cls._object_type, Folder)

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
        from ..impl.file.file import File

        return cls.get_children_typings(cls._object_type, File)

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        _json = super().to_json(deep, **kwargs)

        file_type: Type[File] = self.get_type()

        # Add the list of default extensions for the file
        _json["supported_extensions"] = file_type.supported_extensions

        return _json
