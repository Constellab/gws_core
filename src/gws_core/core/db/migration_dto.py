

from gws_core.core.model.model_dto import BaseModelDTO


class MigrationDTO(BaseModelDTO):
    version: str
    short_description: str
