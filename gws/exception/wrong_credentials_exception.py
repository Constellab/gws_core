
# Credentials error
from fastapi import status

from .base_http_exception import BaseHTTPException
from .gws_exceptions import GWSException


class WrongCredentialsException(BaseHTTPException):

    def __init__(self) -> None:
        super().__init__(
            http_status_code=status.HTTP_401_UNAUTHORIZED,
            detail=GWSException.WRONG_CREDENTIALS.value,
            unique_code=GWSException.WRONG_CREDENTIALS.name,
            headers={"WWW-Authenticate": "Bearer"})
