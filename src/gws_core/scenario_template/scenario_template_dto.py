
from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.protocol.protocol_dto import ProtocolGraphConfigDTO


class ScenarioTemplateDTO(ModelWithUserDTO):
    name: str
    version: int
    description: RichTextDTO | None


# DTO used when downloading a scenario template
class ScenarioTemplateExportDTO(BaseModelDTO):
    id: str
    name: str
    version: int
    description: RichTextDTO | None
    data: ProtocolGraphConfigDTO
