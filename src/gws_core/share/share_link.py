# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from enum import Enum
from typing import Type

from peewee import CharField

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.model.db_field import DateTimeUTC
from gws_core.core.model.model import Model
from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.resource.resource_model import ResourceModel


class ShareLinkType(Enum):
    RESOURCE = "RESOURCE"


class ShareLink(ModelWithUser):

    _table_name = 'gws_share_link'

    entity_id: str = CharField(null=True, max_length=36)

    entity_type: ShareLinkType = EnumField(choices=ShareLinkType)

    valid_until = DateTimeUTC()

    token: str = CharField(null=True, max_length=100, unique=True)

    @classmethod
    def find_by_token_and_check(cls, token: str) -> 'ShareLink':
        """Method that find a shared entity link by its token and check if it is valid
        """

        shared_entity_link: ShareLink = cls.get_or_none(token=token)

        if not shared_entity_link:
            raise BadRequestException("Invalid link")

        return shared_entity_link

    @classmethod
    def find_by_entity_type_and_id_and_check(
            cls, entity_type: ShareLinkType, entity_id: str) -> 'ShareLink':
        """Method that find a shared entity link by its entity id and type and check if it is valid
        """

        shared_entity_link: ShareLink = cls.find_by_entity_type_and_id(
            entity_type=entity_type, entity_id=entity_id)

        if not shared_entity_link:
            raise BadRequestException("Share link not found")

        return shared_entity_link

    @classmethod
    def find_by_entity_type_and_id(cls, entity_type: ShareLinkType, entity_id: str) -> 'ShareLink':
        """Method that find a shared entity link by its entity id and type
        """
        return cls.get_or_none((cls.entity_type == entity_type) & (cls.entity_id == entity_id))

    @classmethod
    def get_model(cls, entity_id: str, entity_type: ShareLinkType) -> Model:
        """Method that return the model for a given entity type
        """

        model_type: Type[Model] = cls._get_model_type(entity_type)

        return model_type.get_by_id(entity_id)

    @classmethod
    def get_model_and_check(cls, entity_id: str, entity_type: ShareLinkType) -> Model:
        """Method that return the model for a given entity type and check if it exists
        """

        model_type: Type[Model] = cls._get_model_type(entity_type)

        return model_type.get_by_id_and_check(entity_id)

    @classmethod
    def _get_model_type(cls, entity_type: ShareLinkType) -> Type[Model]:
        """Method that return the model type for a given entity type
        """

        if entity_type == ShareLinkType.RESOURCE:
            return ResourceModel
        else:
            raise BadRequestException(f"Entity type {entity_type} is not supported")

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        json_ = super().to_json(deep, **kwargs)

        # add the info of the associated entity if it exists
        entity = self.get_model(self.entity_id, self.entity_type)
        if entity:
            if isinstance(entity, ResourceModel):
                json_['entity_name'] = entity.name
            json_['status'] = 'SUCCESS'
        else:
            json_['status'] = 'ERROR'

        return json_

    # generate unique key with entity_id and entity_type
    class Meta:
        indexes = (
            (("entity_id", "entity_type"), True),
        )