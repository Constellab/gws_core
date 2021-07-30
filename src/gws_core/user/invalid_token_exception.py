# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi import status

from ..core.exception import BaseHTTPException, GWSException


class InvalidTokenException(BaseHTTPException):

    def __init__(self) -> None:
        super().__init__(
            http_status_code=status.HTTP_403_FORBIDDEN,
            detail=GWSException.INVALID_TOKEN.value,
            unique_code=GWSException.INVALID_TOKEN.name,
            headers={"WWW-Authenticate": "Bearer"})
