

from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from gws_core.core.model.model_dto import BaseModelDTO, ModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.external_lab.external_lab_dto import ExternalLabWithUserInfo
from gws_core.resource.resource_dto import ResourceModelDTO
from gws_core.scenario.scenario_zipper import ZipScenarioInfo
from gws_core.user.user_dto import UserDTO


class ShareLinkEntityType(Enum):
    RESOURCE = "RESOURCE"
    SCENARIO = "SCENARIO"


class ShareLinkType(Enum):
    # if the link is public, it can be accessed by anyone
    PUBLIC = "PUBLIC"
    # the link was shared with space and can only be accessed by the space members
    SPACE = "SPACE"


# Define if the resource is shared as a sender or a receiver
class SharedEntityMode(Enum):
    SENT = "SENT"
    RECEIVED = "RECEIVED"


class ShareLinkDTO(ModelWithUserDTO):
    entity_id: str
    entity_type: ShareLinkEntityType
    valid_until: Optional[datetime] = None
    download_link: str
    preview_link: Optional[str] = None
    status: Literal["SUCCESS", "ERROR"]
    entity_name: Optional[str] = None
    link_type: ShareLinkType


class GenerateShareLinkDTO(BaseModelDTO):
    entity_id: str
    entity_type: ShareLinkEntityType
    valid_until: Optional[datetime] = None


class UpdateShareLinkDTO(BaseModelDTO):
    valid_until: Optional[datetime] = None


class ShareEntityInfoDTO(ModelDTO):
    share_mode: SharedEntityMode
    lab_id: str
    lab_name: str
    user_id: str
    user_firstname: str
    user_lastname: str
    space_id: Optional[str] = None
    space_name: Optional[str] = None
    created_by: UserDTO


class ShareEntityInfoReponseDTO(BaseModelDTO):
    version: int
    entity_type: ShareLinkEntityType
    entity_id: str


class ShareResourceInfoReponseDTO(ShareEntityInfoReponseDTO):
    entity_object: List[ResourceModelDTO]
    # full route to call to zip the entity
    zip_entity_route: str


class ShareScenarioInfoReponseDTO(ShareEntityInfoReponseDTO):
    entity_object: ZipScenarioInfo
    resource_route: str
    token: str
    origin: ExternalLabWithUserInfo

    def get_resource_route(self, resource_id: str) -> str:
        return self.resource_route.replace('[RESOURCE_ID]', resource_id)


class ShareResourceZippedResponseDTO(BaseModelDTO):
    version: int
    entity_type: ShareLinkEntityType
    entity_id: str
    # id of the resource that contains the zip file of the shared entity
    zipped_entity_resource_id: str
    # full route to call to download the entity
    download_entity_route: str


class ShareEntityCreateMode(Enum):
    KEEP_ID = "KEEP_ID"
    NEW_ID = "NEW_ID"


class GenerateUserAccessTokenForSpaceResponse(BaseModelDTO):
    valid_until: datetime
    access_url: str
