from fastapi import HTTPException, status


class UnauthorizedException(HTTPException):
    """
    Generic unauthorized exception to throw a 401 error
    """

    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=message)