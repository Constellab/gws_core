# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import final

from peewee import CharField

from ...model.typing_register_decorator import typing_registrator
from ...resource.resource_model import ResourceModel
from .fs_node import FSNode
from .local_file_store import LocalFileStore


@final
@typing_registrator(unique_name="FSNodeModel", object_type="MODEL", hide=True)
class FSNodeModel(ResourceModel):
    path = CharField(null=True, index=True, unique=True)
    file_store_uri = CharField(null=True, index=True)
    _table_name = "gws_fs_node_resource"

    def send_fields_to_resource(self, resource: FSNode):
        super().send_fields_to_resource(resource)
        resource.path = self.path
        resource.file_store_uri = self.file_store_uri

    def receive_fields_from_resource(self, resource: FSNode):
        super().receive_fields_from_resource(resource)
        self.path = resource.path
        self.file_store_uri = resource.file_store_uri

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        _json = super().to_json(deep=deep,  **kwargs)
        # _json["name"] = FileHelper.get_name_with_extension(self.path)
        _json["is_file"] = True
        return _json

    @classmethod
    def from_resource(cls, resource: FSNode) -> ResourceModel:
        """Create a new ResourceModel from a resource

        :return: [description]
        :rtype: [type]
        """
        # add the file to the local storage
        node: FSNode = LocalFileStore.get_default_instance().add_node(resource, resource.name)

        return super().from_resource(node)
