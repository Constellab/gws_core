

from typing import Optional

from gws_core.core.model.model_dto import BaseModelDTO


class UserCredentialsDTO(BaseModelDTO):
    email: str
    password: str
    captcha: Optional[str]


class UserCredentials2Fa(BaseModelDTO):
    twoFAUrlCode: str
    twoFACode: str
