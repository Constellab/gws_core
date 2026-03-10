from enum import Enum
from typing import Literal

from gws_core.core.model.model_dto import BaseModelDTO

LabEnvironment = Literal["ON_CLOUD", "DESKTOP", "LOCAL"]


class LabMode(Enum):
    PROD = "prod"
    DEV = "dev"


class LabDTO(BaseModelDTO):
    """DTO representing a lab (local or external)."""

    id: str
    name: str
    is_current_lab: bool
    environment: LabEnvironment | None = None
    domain: str | None = None
    space_id: str | None = None
    space_name: str | None = None
