from fastapi import status

from .base_http_exception import BaseHTTPException


class UnauthorizedException(BaseHTTPException):
    """
    Generic unauthorized exception to throw a 401 error
    """

    def __init__(self, detail: str, unique_code: str = None) -> None:
        super().__init__(
            http_status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail, unique_code=unique_code)
