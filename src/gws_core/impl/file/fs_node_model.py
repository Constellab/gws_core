# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import TYPE_CHECKING, List, Union, final

from peewee import BigIntegerField, BooleanField, CharField

from gws_core.impl.file.file_helper import FileHelper

from ...core.model.model import Model
from ...impl.file.file_store import FileStore

if TYPE_CHECKING:
    from ...resource.resource_model import ResourceModel


@final
class FSNodeModel(Model):
    """Table link to ResourceModel to store all the file that are in a file_store

    :param Model: [description]
    :type Model: [type]
    """
    path = CharField(null=True, unique=True)
    file_store_id = CharField(null=True, index=True)
    size = BigIntegerField(null=True)
    is_symbolic_link = BooleanField(null=False, default=False)

    _table_name = "gws_fs_node"

    def delete_instance(self, delete_file: bool = True, *args, **kwargs):

        # if the file is a real file, not a symbolic link, delete it
        if delete_file:
            self.delete_object()

        return super().delete_instance(*args, **kwargs)

    def delete_object(self):
        """Delete file in the server not in the database

        :return: _description_
        :rtype: _type_
        """
        # if the file is a real file, not a symbolic link, delete it
        if not self.is_symbolic_link:
            # TODO add support for other FileStore
            file_store: FileStore = FileStore.get_default_instance()
            file_store.delete_node_path(self.path)

    def get_file_store(self) -> FileStore:
        return FileStore.get_by_id_and_check(self.file_store_id)

    @classmethod
    def find_by_path(cls, path: str) -> Union['FSNodeModel', None]:
        return cls.select().where(cls.path == path).first()

    @classmethod
    def path_start_with(cls, path: str) -> List['FSNodeModel']:
        return list(cls.select().where(cls.path.startswith(path)))

    def get_resource_model(self) -> 'ResourceModel':
        from gws_core.resource.resource_model import ResourceModel
        return ResourceModel.get(ResourceModel.fs_node_model == self)

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        return {
            "id": self.id,
            "size": self.size,
            "is_file": FileHelper.is_file(self.path),
            "name": FileHelper.get_name_with_extension(self.path),
            "path": self.path,
        }
