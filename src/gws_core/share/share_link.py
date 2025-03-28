

from datetime import datetime
from typing import Optional, Type

from peewee import CharField

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.model.db_field import DateTimeUTC
from gws_core.core.model.model import Model
from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.core.service.front_service import FrontService
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.settings import Settings
from gws_core.resource.resource_model import ResourceModel
from gws_core.scenario.scenario import Scenario
from gws_core.share.shared_dto import (ShareLinkDTO, ShareLinkEntityType,
                                       ShareLinkType)


class ShareLink(ModelWithUser):

    _table_name = 'gws_share_link'

    entity_id: str = CharField(null=True, max_length=36)

    entity_type: ShareLinkEntityType = EnumField(choices=ShareLinkEntityType)

    valid_until: datetime = DateTimeUTC(null=True)

    token: str = CharField(null=True, max_length=100, unique=True)

    link_type: ShareLinkType = EnumField(choices=ShareLinkType, default=ShareLinkType.PUBLIC)

    @classmethod
    def find_by_token_and_check(cls, token: str) -> 'ShareLink':
        """Method that find a shared entity link by its token and check if it is valid
        """

        shared_entity_link: ShareLink = cls.get_or_none(token=token)

        if not shared_entity_link:
            raise BadRequestException("Invalid link")

        return shared_entity_link

    @classmethod
    def find_by_entity_type_and_id_and_check(cls, entity_type: ShareLinkEntityType,
                                             entity_id: str,
                                             link_type: ShareLinkType) -> 'ShareLink':
        """Method that find a shared entity link by its entity id and type and check if it is valid
        """

        shared_entity_link: ShareLink = cls.find_by_entity_type_and_id(
            entity_type=entity_type, entity_id=entity_id, link_type=link_type)

        if not shared_entity_link:
            raise BadRequestException("Share link not found")

        return shared_entity_link

    @classmethod
    def find_by_entity_type_and_id(cls, entity_type: ShareLinkEntityType,
                                   entity_id: str,
                                   link_type: ShareLinkType) -> Optional['ShareLink']:
        """Method that find a shared entity link by its entity id and type
        """
        return cls.get_or_none((cls.entity_type == entity_type) & (cls.entity_id == entity_id) &
                               (cls.link_type == link_type))

    @classmethod
    def get_model(cls, entity_id: str, entity_type: ShareLinkEntityType) -> Model:
        """Method that return the model for a given entity type
        """

        model_type: Type[Model] = cls._get_model_type(entity_type)

        return model_type.get_by_id(entity_id)

    @classmethod
    def get_model_and_check(cls, entity_id: str, entity_type: ShareLinkEntityType) -> Model:
        """Method that return the model for a given entity type and check if it exists
        """

        model_type: Type[Model] = cls._get_model_type(entity_type)

        return model_type.get_by_id_and_check(entity_id)

    @classmethod
    def _get_model_type(cls, entity_type: ShareLinkEntityType) -> Type[Model]:
        """Method that return the model type for a given entity type
        """

        if entity_type == ShareLinkEntityType.RESOURCE:
            return ResourceModel
        elif entity_type == ShareLinkEntityType.SCENARIO:
            return Scenario
        else:
            raise BadRequestException(f"Entity type {entity_type} is not supported")

    def to_dto(self) -> ShareLinkDTO:
        link_dto = ShareLinkDTO(
            id=self.id,
            created_at=self.created_at,
            created_by=self.created_by.to_dto(),
            last_modified_at=self.last_modified_at,
            last_modified_by=self.last_modified_by.to_dto(),
            entity_id=self.entity_id,
            entity_type=self.entity_type,
            valid_until=self.valid_until,
            download_link=self.get_download_link(),
            preview_link=self.get_public_link(),
            status='SUCCESS',
            link_type=self.link_type,
        )

        # add the info of the associated entity if it exists
        entity = self.get_model(self.entity_id, self.entity_type)
        if entity:
            if isinstance(entity, ResourceModel):
                link_dto.entity_name = entity.name
            elif isinstance(entity, Scenario):
                link_dto.entity_name = entity.title
            link_dto.status = 'SUCCESS'
        else:
            link_dto.status = 'ERROR'

        return link_dto

    def get_download_link(self) -> str:
        if self.entity_type == ShareLinkEntityType.RESOURCE:
            return f"{Settings.get_lab_api_url()}/{Settings.core_api_route_path()}/share/resource/{self.token}"
        elif self.entity_type == ShareLinkEntityType.SCENARIO:
            return f"{Settings.get_lab_api_url()}/{Settings.core_api_route_path()}/share/scenario/{self.token}"

    def get_public_link(self) -> str | None:
        if self.entity_type == ShareLinkEntityType.RESOURCE:
            return FrontService.get_resource_open_url(self.token)
        elif self.entity_type == ShareLinkEntityType.SCENARIO:
            return None

    def get_space_link(self, user_access_token: str) -> str | None:
        if self.entity_type == ShareLinkEntityType.RESOURCE:
            return FrontService.get_resource_open_space_url(self.token, user_access_token)
        else:
            raise BadRequestException("Space link is not supported for this entity type")

    def is_valid(self) -> bool:
        return self.valid_until is None or self.valid_until > DateHelper.now_utc()

    def is_valid_at(self, valid_until_date: datetime) -> bool:
        if not valid_until_date:
            return self.valid_until is None
        return self.valid_until is None or self.valid_until > valid_until_date

    @classmethod
    def is_lab_share_resource_link(cls, link: str) -> bool:
        return cls._is_lab_share_entity_link(link) and link.find('share/') != -1

    @classmethod
    def is_lab_share_scenario_link(cls, link: str) -> bool:
        return cls._is_lab_share_entity_link(link) and link.find('share/scenario/') != -1

    @classmethod
    def _is_lab_share_entity_link(cls, link: str) -> bool:
        settings = Settings.get_instance()

        # is the url does not contains core-api, it is not a share link form a lab
        if not link.find(settings.core_api_route_path()):
            return False

        # specific case for dev env, accept if the link is from this lab
        if settings.is_local_env() and link.startswith(
                settings.get_lab_api_url()):
            return True

        # check if the link is from correct sub domain
        return link.startswith(f'https://{Settings.prod_api_sub_domain()}') or link.startswith(
            f'https://{Settings.dev_api_sub_domain()}')

    # generate unique key with entity_id and entity_type

    class Meta:
        table_name = 'gws_share_link'
        indexes = (
            (("entity_id", "entity_type", "link_type"), True),
        )
