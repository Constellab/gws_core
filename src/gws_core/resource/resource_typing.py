# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Literal, Type

from gws_core.core.model.base import Base
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

    def model_type_to_json(self, model_t: Type[Base]) -> dict:
        return {
            "doc": self.get_model_type_doc(),
        }


class FileTyping(ResourceTyping):

    @classmethod
    def get_typings(cls) -> List['ResourceTyping']:
        from ..impl.file.file import File

        return cls.get_children_typings(cls._object_type, File)
