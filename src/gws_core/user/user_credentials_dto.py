

from typing import Optional

from pydantic import BaseModel


class UserCredentialsDTO(BaseModel):
    email: str
    password: str
    captcha: Optional[str]


class UserCredentials2Fa(BaseModel):
    twoFAUrlCode: str
    twoFACode: str
