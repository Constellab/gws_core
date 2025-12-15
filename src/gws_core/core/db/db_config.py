from typing import Literal

from gws_core.core.model.model_dto import BaseModelDTO

SupportedDbEngine = Literal["mysql", "mariadb"]

DbMode = Literal["prod", "dev", "test"]


class DbConfig(BaseModelDTO):
    user: str
    password: str
    host: str
    port: int
    db_name: str
    engine: SupportedDbEngine
