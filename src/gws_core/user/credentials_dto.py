# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from pydantic import BaseModel


class CredentialsDTO(BaseModel):
    email: str
    password: str
    captcha: str


class Credentials2Fa(BaseModel):
    twoFAUrlCode: str
    twoFACode: str
