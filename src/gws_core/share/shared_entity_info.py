

from peewee import CharField, ForeignKeyField

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.model.model import Model
from gws_core.external_lab.external_lab_dto import ExternalLabWithUserInfo
from gws_core.share.shared_dto import SharedEntityMode, ShareEntityInfoDTO
from gws_core.user.user import User


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
    created_by: User = ForeignKeyField(User, null=True, backref='+')

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

    @classmethod
    def create_from_lab_info(cls, entity_id: str, mode: SharedEntityMode,
                             lab_info: ExternalLabWithUserInfo, created_by: User) -> None:
        """Method that log the resource origin for each imported resources
        """

        shared_entity = cls()
        shared_entity.entity = entity_id
        shared_entity.share_mode = mode
        shared_entity.lab_id = lab_info.lab_id
        shared_entity.lab_name = lab_info.lab_name
        shared_entity.user_id = lab_info.user_id
        shared_entity.user_firstname = lab_info.user_firstname
        shared_entity.user_lastname = lab_info.user_lastname
        shared_entity.space_id = lab_info.space_id
        shared_entity.space_name = lab_info.space_name
        shared_entity.created_by = created_by
        shared_entity.save()

    def to_dto(self) -> ShareEntityInfoDTO:
        return ShareEntityInfoDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            share_mode=self.share_mode,
            lab_id=self.lab_id,
            lab_name=self.lab_name,
            user_id=self.user_id,
            user_firstname=self.user_firstname,
            user_lastname=self.user_lastname,
            space_id=self.space_id,
            space_name=self.space_name,
            created_by=self.created_by.to_dto() if self.created_by else None,
        )
