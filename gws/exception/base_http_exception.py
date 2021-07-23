
from typing import Dict

from fastapi import HTTPException


class BaseHTTPException(HTTPException):
    """
    Generic exception
    All the exception that extends this exceptions are considered a excepted exceptions and
    those are not logged in the console nor the logging file
    """

    def __init__(self, http_status_code: int, detail: str, unique_code: str = None,
                 headers: Dict = None) -> None:
        """[sumpopmary]

        Arguments:
            status_code {int} -- [description]
            code {str} -- [description]
        """
        super().__init__(status_code=http_status_code, detail=detail)
        self.detail = detail
        self.unique_code = unique_code
        self.headers = headers
