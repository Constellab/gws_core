
from fastapi import status

from .base_http_exception import BaseHTTPException


class BadRequestException(BaseHTTPException):
    """
    Generic exception to throw a 400 error
    """

    def __init__(self, detail: str, unique_code: str = None) -> None:
        super().__init__(
            http_status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail, unique_code=unique_code)
