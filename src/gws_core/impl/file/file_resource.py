

from typing import Type

from peewee import CharField

from ...model.typing_manager import TypingManager
from ...model.typing_register_decorator import TypingDecorator
from ...resource.resource_model import ResourceModel
from .file import File


@TypingDecorator(unique_name="FileResource", object_type="GWS_CORE", hide=True)
class FileResource(ResourceModel):
    file_store_uri = CharField(null=True, index=True)
    path = CharField(null=True, index=True, unique=True)

    _resource: File
    _table_name = "gws_file_resource"

    def _instantiate_resource(self) -> File:
        """
        Create the Resource object from the resource_typing_name
        """
        resource_type: Type[File] = TypingManager.get_type_from_name(self.resource_typing_name)
        file: File = resource_type(data=self.data)
        file.path = self.path
        file.file_store_uri = self.file_store_uri

    # override the from resource  to set data to empty dict and set path from File
    @classmethod
    def from_resource(cls, resource: File) -> 'FileResource':
        file_resource: FileResource = FileResource()
        file_resource.resource_typing_name = resource._typing_name
        file_resource._resource = resource  # set the resource into the resource model
        file_resource.data = {}
        file_resource.path = resource.path
        file_resource.file_store_uri = resource.file_store_uri

        return file_resource
