from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.settings import Settings
from gws_core.credentials.credentials_type import CredentialsDataLab
from gws_core.lab.lab_model.lab_enums import LabEnvironment, LabMode


class LabDTO(BaseModelDTO):
    """DTO representing a lab (local or external)."""

    id: str
    lab_id: str
    name: str
    is_current_lab: bool = False
    mode: LabMode
    environment: LabEnvironment
    domain: str | None = None
    space_id: str | None = None
    space_name: str | None = None
    credentials_id: str | None = None

    def get_api_url(self) -> str:
        """Build the API URL for this lab from its domain and mode.

        Uses the prod or dev API sub-domain based on the lab's mode.
        """
        if not self.domain:
            raise ValueError("Cannot retrieve lab API URL: lab domain is not set")
        if self.mode == LabMode.DEV:
            sub_domain = Settings.dev_api_sub_domain()
        else:
            sub_domain = Settings.prod_api_sub_domain()
        return f"https://{sub_domain}.{self.domain}"


class LabDTOWithCredentials(BaseModelDTO):
    """DTO containing a lab and its resolved credentials data."""

    lab: LabDTO
    credentials_data: CredentialsDataLab | None = None


class CreateLabFromCodeDTO(BaseModelDTO):
    """DTO for creating a lab from a unique code."""

    code: str
    lab: LabDTO
