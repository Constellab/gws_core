

import inspect
from typing import Any, List, Literal, Type

from gws_core.core.utils.refloctor_types import MethodDoc
from gws_core.core.utils.utils import Utils
from gws_core.model.typing_dto import TypingDTO
from gws_core.resource.resource_typing_dto import (ResourceTypingDTO,
                                                   ResourceTypingMethodDTO)

from ..core.utils.reflector_helper import ReflectorHelper
from ..model.typing import Typing
from ..model.typing_dto import TypingObjectType
from ..resource.view.view_helper import ViewHelper
from ..resource.view.view_meta_data import ResourceViewMetaData

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

    def to_full_dto(self) -> ResourceTypingDTO:
        typing_dto = super().to_full_dto()

        return ResourceTypingDTO(
            **typing_dto.dict(),
            methods=self.get_class_methods_docs()
        )

    def get_class_methods_docs(self) -> ResourceTypingMethodDTO:
        type_: Type = self.get_type()
        if not inspect.isclass(type_):
            return None
        methods: Any = inspect.getmembers(type_, predicate=inspect.isfunction)
        views_methods: List[ResourceViewMetaData] = ViewHelper.get_views_of_resource_type(type_)
        views_methods_dto = [m.to_dto() for m in views_methods]
        func_methods: Any = [method for method in methods if not ReflectorHelper.is_decorated_with_view(method)]
        public_func_methods: Any = [(m[0], m[1])
                                    for m in func_methods if not m[0].startswith('_') or m[0] == '__init__']
        funcs: List[MethodDoc] = ReflectorHelper.get_methods_doc(public_func_methods)
        return ResourceTypingMethodDTO(
            funcs=funcs if len(funcs) > 0 else None,
            views=views_methods_dto if len(views_methods_dto) > 0 else None
        )


class FileTyping(ResourceTyping):

    @classmethod
    def get_typings(cls) -> List['ResourceTyping']:
        from ..impl.file.file import File

        return cls.get_children_typings(cls._object_type, File)

    def to_dto(self) -> TypingDTO:
        from ..impl.file.file import File
        typing_dto = super().to_dto()

        # retrieve the task python type
        model_t: Type[File] = self.get_type()

        if model_t and Utils.issubclass(model_t, File):
            typing_dto.additional_data = {"default_extensions": model_t.__default_extensions__ or []}

        return typing_dto
