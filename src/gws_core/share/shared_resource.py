# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from enum import Enum

from peewee import CharField, ForeignKeyField

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.resource.resource_model import ResourceModel


# Define if the resource is shared as a sender or a receiver
class SharedResourceMode(Enum):
    SENT = "SENT"
    RECEIVED = "RECEIVED"


class SharedResource(ModelWithUser):

    _table_name = 'gws_shared_resource'

    share_mode: SharedResourceMode = EnumField(choices=SharedResourceMode)

    resource: ResourceModel = ForeignKeyField(ResourceModel, backref="+")

    lab_id: str = CharField()

    lab_name: str = CharField()

    user_id: str = CharField()

    user_firstname: str = CharField()

    user_lastname: str = CharField()

    space_id: str = CharField(null=True)

    space_name: str = CharField(null=True)

    @classmethod
    def get_and_check_resource_origin(cls, resource_id: str) -> 'SharedResource':
        """Method that check if the resource is shared and return the origin information
        """
        shared_resource = cls.get_or_none(
            cls.resource == resource_id and cls.share_mode == SharedResourceMode.RECEIVED)

        if shared_resource is None:
            raise ValueError(f"The resource with id '{resource_id}' was not imported from another lab")

        return shared_resource
