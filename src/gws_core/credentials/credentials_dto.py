

from typing import Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.model.model_with_user_dto import ModelWithUserDTO

from .credentials_type import CredentialsType


class SaveCredentialDTO(BaseModelDTO):
    name: str
    type: CredentialsType
    description: Optional[str] = None
    data: dict


class CredentialDTO(ModelWithUserDTO):
    name: str
    type: CredentialsType
    description: Optional[str] = None
