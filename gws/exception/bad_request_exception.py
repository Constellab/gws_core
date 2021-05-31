
from fastapi import HTTPException, status


class BadRequestException(HTTPException):
    """
    Generic exception to throw a 400 error
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message)