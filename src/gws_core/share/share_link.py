from datetime import datetime
from typing import Optional

from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.model.model import Model
from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.core.model.typed_db_field import (
    NullableDateTimeUTC,
    TypedCharField,
    TypedEnumField,
)
from gws_core.core.service.front_service import FrontService
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.settings import Settings
from gws_core.resource.resource_model import ResourceModel
from gws_core.scenario.scenario import Scenario
from gws_core.share.shared_dto import ShareLinkDTO, ShareLinkEntityType, ShareLinkType
from gws_core.user.unique_code_service import (
    CodeObject,
    InvalidUniqueCodeException,
    UniqueCodeService,
)


class ShareLink(ModelWithUser):
    entity_id = TypedCharField(max_length=36)

    entity_type = TypedEnumField(choices=ShareLinkEntityType)

    valid_until = NullableDateTimeUTC()

    token = TypedCharField(max_length=100, unique=True)

    link_type = TypedEnumField(choices=ShareLinkType, default=ShareLinkType.PUBLIC)

    # Lifetime of a single-use space access code (was ShareLinkService.SPACE_ACCESS_DURATION_SECONDS).
    SPACE_ACCESS_DURATION_SECONDS = 60 * 60  # 1 hour
    # Key under which this share link's id is stored in a space access code payload, so consumption
    # can confirm the code was minted for this exact link.
    SPACE_ACCESS_SHARE_LINK_ID_KEY = "share_link_id"

    @classmethod
    def find_by_token_and_check(cls, token: str) -> "ShareLink":
        """Method that find a shared entity link by its token and check if it is valid"""

        shared_entity_link: ShareLink = cls.get_or_none(token=token)

        if not shared_entity_link:
            raise BadRequestException("Invalid link")

        return shared_entity_link

    @classmethod
    def find_by_entity_type_and_id_and_check(
        cls, entity_type: ShareLinkEntityType, entity_id: str, link_type: ShareLinkType
    ) -> "ShareLink":
        """Method that find a shared entity link by its entity id and type and check if it is valid"""

        shared_entity_link = cls.find_by_entity_type_and_id(
            entity_type=entity_type, entity_id=entity_id, link_type=link_type
        )

        if not shared_entity_link:
            raise BadRequestException("Share link not found")

        return shared_entity_link

    @classmethod
    def find_by_entity_type_and_id(
        cls, entity_type: ShareLinkEntityType, entity_id: str, link_type: ShareLinkType
    ) -> Optional["ShareLink"]:
        """Method that find a shared entity link by its entity id and type"""
        return cls.get_or_none(
            (cls.entity_type == entity_type)
            & (cls.entity_id == entity_id)
            & (cls.link_type == link_type)
        )

    @classmethod
    def get_model(cls, entity_id: str, entity_type: ShareLinkEntityType) -> Model | None:
        """Method that return the model for a given entity type"""

        model_type: type[Model] = cls._get_model_type(entity_type)

        return model_type.get_by_id(entity_id)

    @classmethod
    def get_model_and_check(cls, entity_id: str, entity_type: ShareLinkEntityType) -> Model:
        """Method that return the model for a given entity type and check if it exists"""

        model_type: type[Model] = cls._get_model_type(entity_type)

        return model_type.get_by_id_and_check(entity_id)

    @classmethod
    def _get_model_type(cls, entity_type: ShareLinkEntityType) -> type[Model]:
        """Method that return the model type for a given entity type"""

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
            status="SUCCESS",
            link_type=self.link_type,
        )

        # add the info of the associated entity if it exists
        entity = self.get_model(self.entity_id, self.entity_type)
        if entity:
            if isinstance(entity, ResourceModel):
                link_dto.entity_name = entity.name
            elif isinstance(entity, Scenario):
                link_dto.entity_name = entity.title
            link_dto.status = "SUCCESS"
        else:
            link_dto.status = "ERROR"

        return link_dto

    def get_download_link(self) -> str:
        if self.entity_type == ShareLinkEntityType.RESOURCE:
            return f"{Settings.get_lab_api_url()}/{Settings.core_api_route_path()}/share/resource/{self.token}"
        elif self.entity_type == ShareLinkEntityType.SCENARIO:
            return f"{Settings.get_lab_api_url()}/{Settings.core_api_route_path()}/share/scenario/{self.token}"
        else:
            raise BadRequestException(f"Entity type {self.entity_type} is not supported")

    def get_public_link(self) -> str | None:
        if self.entity_type == ShareLinkEntityType.RESOURCE:
            return FrontService().get_resource_open_url(self.token)
        elif self.entity_type == ShareLinkEntityType.SCENARIO:
            return None
        else:
            raise BadRequestException(f"Entity type {self.entity_type} is not supported")

    def generate_space_access_code(self, user_id: str) -> str:
        """Mint a single-use, short-lived code granting access to this (space) share link.

        The code is bound to this link's id and to the given user; it is consumed once when the
        shared resource/app is opened (see ``check_space_access_code``). The space requests a fresh
        code (for the space-authenticated user) right before each open, so single-use is safe.
        Replaces the former in-memory ShareLinkSpaceAccess store.

        :param user_id: the user the code authenticates (the space-authenticated visitor)
        :return: the one-time space access code
        """
        return UniqueCodeService.generate_code(
            user_id,
            {self.SPACE_ACCESS_SHARE_LINK_ID_KEY: self.id},
            self.SPACE_ACCESS_DURATION_SECONDS,
        )

    def check_space_access_code(self, space_access_code: str) -> str:
        """Consume a space access code and return the user id it was minted for.

        Confirms the code was minted for *this* share link (bound id) before trusting it, so a code
        for link A cannot open link B.

        :param space_access_code: the single-use code (consumed here)
        :return: the user id the code authenticates
        :raises InvalidUniqueCodeException: if the code is invalid, expired, or for another link
        """
        code_obj: CodeObject = UniqueCodeService.check_code(space_access_code)
        if code_obj.obj.get(self.SPACE_ACCESS_SHARE_LINK_ID_KEY) != self.id:
            raise InvalidUniqueCodeException()
        return code_obj.user_id

    def get_space_link(self, space_access_code: str) -> str:
        if self.entity_type != ShareLinkEntityType.RESOURCE:
            raise BadRequestException("Space link is not supported for this entity type")

        # When the shared resource is an app, open it through the launcher gateway (stable,
        # iframe-free, cold-starts the app) instead of the datalab resource-open page. The
        # space_access_code is the single-use code the gateway consumes.
        if self._resource_is_app():
            return FrontService().get_app_gateway_url(self.entity_id, code=space_access_code)

        return FrontService().get_resource_open_space_url(self.token, space_access_code)

    def _resource_is_app(self) -> bool:
        """Return True if the shared resource is an app resource."""
        # Local import to avoid a module-level dependency of the share layer on apps.
        from gws_core.apps.app_resource import AppResource

        resource_model = ResourceModel.get_by_id(self.entity_id)
        if resource_model is None:
            return False
        return isinstance(resource_model.get_resource(), AppResource)

    def is_valid(self) -> bool:
        return self.valid_until is None or self.valid_until > DateHelper.now_utc()

    def is_valid_at(self, valid_until_date: datetime | None) -> bool:
        if not valid_until_date:
            return self.valid_until is None
        return self.valid_until is None or self.valid_until > valid_until_date

    @classmethod
    def is_lab_share_resource_link(cls, link: str) -> bool:
        return cls._is_lab_share_entity_link(link) and link.find("share/") != -1

    @classmethod
    def is_lab_share_scenario_link(cls, link: str) -> bool:
        return cls._is_lab_share_entity_link(link) and link.find("share/scenario/") != -1

    @classmethod
    def _is_lab_share_entity_link(cls, link: str) -> bool:
        settings = Settings.get_instance()

        # is the url does not contains core-api, it is not a share link form a lab
        if not link.find(settings.core_api_route_path()):
            return False

        # specific case for dev env, accept if the link is from this lab
        if settings.is_local_or_desktop_env() and link.startswith(settings.get_lab_api_url()):
            return True

        # check if the link is from correct sub domain
        return link.startswith(f"https://{Settings.prod_api_sub_domain()}") or link.startswith(
            f"https://{Settings.dev_api_sub_domain()}"
        )

    # generate unique key with entity_id and entity_type

    class Meta:
        table_name = "gws_share_link"
        is_table = True
        indexes = ((("entity_id", "entity_type", "link_type"), True),)
