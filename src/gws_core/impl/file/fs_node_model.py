# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from enum import Enum
from typing import final

from peewee import CharField

from ...core.model.model import Model
from ...model.typing_register_decorator import typing_registrator


@final
@typing_registrator(unique_name="FSNodeModel", object_type="MODEL", hide=True)
class FSNodeModel(Model):
    """Table link to ResourceModel to store all the file that are in a file_store

    :param Model: [description]
    :type Model: [type]
    """
    path = CharField(null=True, index=True, unique=True)
    file_store_uri = CharField(null=True, index=True)
    _table_name = "gws_fs_node"
