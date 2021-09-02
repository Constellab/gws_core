

from typing import Type

from peewee import CharField

from ...model.typing_manager import TypingManager
from ...model.typing_register_decorator import TypingDecorator
from ...resource.resource_model import ResourceModel
from ...resource.resource_serialized import ResourceSerialized
from .file import File
from .file_helper import FileHelper


@TypingDecorator(unique_name="FileResource", object_type="GWS_CORE", hide=True)
class FileResource(ResourceModel):
    file_store_uri = CharField(null=True, index=True)
    path = CharField(null=True, index=True, unique=True)

    _resource: File
    _table_name = "gws_file_resource"

    def _instantiate_resource(self, new_instance: bool = False) -> File:
        """
        Create the Resource object from the resource_typing_name
        """
        resource_type: Type[File] = TypingManager.get_type_from_name(self.resource_typing_name)
        file: File = resource_type()

        file.deserialize(ResourceSerialized(light_data={"path": self.path, "file_store_uri": self.file_store_uri}))
        return file

    # override the from resource  to set data to empty dict and set path from File
    @classmethod
    def from_resource(cls, resource: File) -> 'FileResource':
        file_resource: FileResource = FileResource()
        file_resource.resource_typing_name = resource._typing_name
        file_resource._resource = resource  # set the resource into the resource model
        file_resource.data = {}

        resource_serialized: ResourceSerialized = cls._serialize_resource(resource)
        file_resource.path = resource_serialized.light_data["path"]
        file_resource.file_store_uri = resource_serialized.light_data["file_store_uri"]
        return file_resource

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        _json = super().to_json(deep=deep,  **kwargs)

        _json["filename"] = FileHelper.get_name_with_extension(self.path)
        _json["is_file"] = True
        return _json
