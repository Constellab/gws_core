

from typing import Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.protocol.protocol_dto import ProtocolGraphConfigDTO


class ScenarioTemplateDTO(ModelWithUserDTO):
    name: str
    version: int
    description: Optional[dict]

# DTO used when downloading a scenario template


class ScenarioTemplateExportDTO(BaseModelDTO):
    id: str
    name: str
    version: int
    description: Optional[dict]
    data: ProtocolGraphConfigDTO
