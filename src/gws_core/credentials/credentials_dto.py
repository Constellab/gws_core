

from typing import Optional

from pydantic import BaseModel

from gws_core.core.model.model_with_user_dto import ModelWithUserDTO

from .credentials_type import CredentialsType


class SaveCredentialDTO(BaseModel):
    name: str
    type: CredentialsType
    description: Optional[str]
    data: dict


class CredentialDTO(ModelWithUserDTO):
    name: str
    type: CredentialsType
    description: Optional[str]
