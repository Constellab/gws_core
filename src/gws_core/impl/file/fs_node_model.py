# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import final

from peewee import CharField

from ...core.model.model import Model
from ...impl.file.file_store import FileStore
from ...model.typing_register_decorator import typing_registrator


@final
@typing_registrator(unique_name="FSNodeModel", object_type="MODEL", hide=True)
class FSNodeModel(Model):
    """Table link to ResourceModel to store all the file that are in a file_store

    :param Model: [description]
    :type Model: [type]
    """
    path = CharField(null=True, unique=True)
    file_store_uri = CharField(null=True, index=True)
    _table_name = "gws_fs_node"

    def delete_instance(self, *args, **kwargs):
        # TODO add support for other FileStore
        file_store: FileStore = FileStore.get_default_instance()

        file_store.delete_node_path(self.path)
        return super().delete_instance(*args, **kwargs)

    def get_file_store(self) -> FileStore:
        return FileStore.get_by_uri_and_check(self.file_store_uri)
