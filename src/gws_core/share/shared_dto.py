# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from datetime import datetime

from pydantic import BaseModel

from gws_core.resource.resource_model import ResourceModel
from gws_core.share.shared_entity import SharedEntityLinkType


class GenerateShareLinkDTO(BaseModel):

    entity_id: str
    entity_type: SharedEntityLinkType
    valid_until: datetime


class DownloadResourceDTO():

    resource_model: ResourceModel
