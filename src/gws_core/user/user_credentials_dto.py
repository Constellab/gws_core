# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from pydantic import BaseModel


class UserCredentialsDTO(BaseModel):
    email: str
    password: str
    captcha: Optional[str]


class UserCredentials2Fa(BaseModel):
    twoFAUrlCode: str
    twoFACode: str
