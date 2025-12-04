from gws_core.core.model.model_dto import BaseModelDTO


class MigrationDTO(BaseModelDTO):
    version: str
    db_unique_name: str
    short_description: str
