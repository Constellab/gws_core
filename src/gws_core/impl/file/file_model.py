# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core.impl.file.local_file_store import LocalFileStore
from gws_core.resource.resource_model import ResourceModel
from peewee import CharField

from ...model.typing_register_decorator import typing_registrator
from .file import File
from .file_helper import FileHelper


@typing_registrator(unique_name="FileModel", object_type="MODEL", hide=True)
class FileModel(ResourceModel):
    path = CharField(null=True, index=True, unique=True)
    file_store_uri = CharField(null=True, index=True)
    _table_name = "gws_file_resource"

    def send_fields_to_resource(self, resource: File):
        super().send_fields_to_resource(resource)
        resource.path = self.path
        resource.file_store_uri = self.file_store_uri

    def receive_fields_from_resource(self, resource: File):
        super().receive_fields_from_resource(resource)
        self.path = resource.path
        self.file_store_uri = resource.file_store_uri

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        _json = super().to_json(deep=deep,  **kwargs)
        _json["filename"] = FileHelper.get_name_with_extension(self.path)
        _json["is_file"] = True
        return _json

    @classmethod
    def from_resource(cls, resource: File) -> ResourceModel:
        """Create a new ResourceModel from a resource

        :return: [description]
        :rtype: [type]
        """
        # add the file to the local storage
        file: File = LocalFileStore.get_default_instance().add_from_file(resource, resource.name)

        return super().from_resource(file)
