# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from enum import Enum

from peewee import CharField, ForeignKeyField

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.model.model import Model
from gws_core.resource.resource_model import ResourceModel


# Define if the resource is shared as a sender or a receiver
class SharedResourceType(Enum):
    SENT = "SENT"
    RECEIVED = "RECEIVED"


class SharedResource(Model):

    _table_name = 'gws_shared_resource'

    entity_type: SharedResourceType = EnumField(choices=SharedResourceType)

    resource_id: str = ForeignKeyField(ResourceModel, backref="+")

    lab_id: str = CharField()

    lab_name: str = CharField()

    user_id: str = CharField()

    user_name: str = CharField()

    space_id: str = CharField()

    space_name: str = CharField()
