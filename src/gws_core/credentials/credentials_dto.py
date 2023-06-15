# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from pydantic import BaseModel

from .credentials_type import CredentialsType


class SaveCredentialDTO(BaseModel):
    name: str
    type: CredentialsType
    description: Optional[str]
    data: dict
