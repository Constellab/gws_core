# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.protocol.protocol_dto import ProtocolConfigDTO


class ProtocolTemplateDTO(ModelWithUserDTO):
    name: str
    version: int
    description: Optional[dict]

# DTO used when downloading a protocol template


class ProtocolTemplateExportDTO(BaseModelDTO):
    id: str
    name: str
    version: int
    description: Optional[dict]
    data: ProtocolConfigDTO
