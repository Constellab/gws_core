# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Literal, Type

from peewee import ModelSelect

from gws_core.core.utils.utils import Utils
from gws_core.model.typing_dict import TypingDict

from ..model.typing import Typing
from ..model.typing_dict import TypingObjectType

# Sub type of resource type
# RESOURCE --> normal resource
ResourceSubType = Literal["RESOURCE"]


class ResourceTyping(Typing):
    """
    ResourceType class.
    """

    _object_type: TypingObjectType = "RESOURCE"

    @classmethod
    def get_folder_types(cls) -> List['ResourceTyping']:
        from ..impl.file.folder import Folder

        return cls.get_children_typings(cls._object_type, Folder)


class FileTyping(ResourceTyping):

    @classmethod
    def get_typings(cls) -> List['ResourceTyping']:
        from ..impl.file.file import File

        return cls.get_children_typings(cls._object_type, File)

    def to_json(self, deep: bool = False, **kwargs) -> TypingDict:
        from ..impl.file.file import File
        json_ = super().to_json(deep, **kwargs)

        # retrieve the task python type
        model_t: Type[File] = self.get_type()

        if model_t and Utils.issubclass(model_t, File):
            json_["additional_info"] = {"default_extensions": model_t.__default_extensions__ or []}

        return json_
