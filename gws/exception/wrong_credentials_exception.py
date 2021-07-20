
# Credentials error
from fastapi import HTTPException, status
from ..logger import Logger

class WrongCredentialsException(HTTPException):

    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"})
        Logger.error(f"{self}")