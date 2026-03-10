from enum import Enum

from gws_core.core.model.model_dto import BaseModelDTO


class LabEnvironment(Enum):
    ON_CLOUD = "ON_CLOUD"
    DESKTOP = "DESKTOP"
    LOCAL = "LOCAL"


class LabMode(Enum):
    PROD = "prod"
    DEV = "dev"


class LabDTO(BaseModelDTO):
    """DTO representing a lab (local or external)."""

    id: str
    lab_id: str
    name: str
    is_current_lab: bool
    mode: LabMode | None = None
    environment: LabEnvironment | None = None
    domain: str | None = None
    space_id: str | None = None
    space_name: str | None = None
