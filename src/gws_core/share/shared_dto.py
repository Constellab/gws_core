# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from datetime import datetime
from typing import Any

from pydantic import BaseModel

from gws_core.resource.resource_model import ResourceModel
from gws_core.share.share_link import ShareLinkType


class GenerateShareLinkDTO(BaseModel):

    entity_id: str
    entity_type: ShareLinkType
    valid_until: datetime


class DownloadResourceDTO():

    resource_model: ResourceModel


class ShareEntityInfoDTO(BaseModel):
    version: int
    entity_type: ShareLinkType
    entity_id: str
    entity_object: Any
    # full route to call to zip the entity
    zip_entity_route: str


class ShareEntityZippedResponseDTO(BaseModel):
    version: int
    entity_type: ShareLinkType
    entity_id: str
    # id of the resource that contains the zip file of the shared entity
    zipped_entity_resource_id: str
    # full route to call to download the entity
    download_entity_route: str
