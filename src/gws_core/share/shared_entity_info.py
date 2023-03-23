# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from enum import Enum

from peewee import CharField, ForeignKeyField

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.model.model import Model
from gws_core.user.user import User


# Define if the resource is shared as a sender or a receiver
class SharedEntityMode(Enum):
    SENT = "SENT"
    RECEIVED = "RECEIVED"


class SharedEntityInfo(Model):
    """Class to store information about an shared entity.
    It stored the origin of the entity if the entity was imported from an external source.
    It store the destination of the entity if the entity was exported to an external source.

    :param Model: _description_
    :type Model: _type_
    :raises ValueError: _description_
    :return: _description_
    :rtype: _type_
    """

    share_mode: SharedEntityMode = EnumField(choices=SharedEntityMode)

    lab_id: str = CharField()

    lab_name: str = CharField()

    user_id: str = CharField()

    user_firstname: str = CharField()

    user_lastname: str = CharField()

    space_id: str = CharField(null=True)

    space_name: str = CharField(null=True)

    # current lab user that
    # In SENT mode is the one who created the share link
    # In RECEIVED mode, is the one that imported the entity
    created_by = ForeignKeyField(User, null=True, backref='+')

    # override on children classes
    entity: Model = None

    @classmethod
    def get_and_check_entity_origin(cls, entity_id: str) -> 'SharedEntityInfo':
        """Method that check if the entity is shared and return the origin information
        """
        shared_resource = cls.get_or_none(
            (cls.entity == entity_id) &
            (cls.share_mode == SharedEntityMode.RECEIVED))

        if shared_resource is None:
            raise BadRequestException("Information about lab import does not exist")

        return shared_resource

    @classmethod
    def already_shared_with_lab(cls, entity_id: str, lab_id: str) -> bool:
        """Method that check if the entity is already shared with the lab
        """
        return cls.get_or_none(
            (cls.entity == entity_id) &
            (cls.share_mode == SharedEntityMode.SENT) &
            (cls.lab_id == lab_id)) is not None

    @classmethod
    def get_sents(cls, entity_id: str) -> 'SharedEntityInfo':
        """Method that return the receivers of the entity
        """
        return cls.select().where(cls.entity == entity_id, cls.share_mode == SharedEntityMode.SENT).order_by(
            cls.created_at.desc())

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        json_ = super().to_json(deep, **kwargs)

        # add the created by and last_modified_by
        if self.created_by:
            json_["created_by"] = self.created_by.to_json()

        return json_
