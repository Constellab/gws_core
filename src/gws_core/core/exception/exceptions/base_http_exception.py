# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict
from fastapi import HTTPException

class BaseHTTPException(HTTPException):
    """
    Generic exception
    All the exception that extends this exceptions are considered a excepted exceptions and
    those are not logged in the console nor the logging file
    """

    def __init__(self, http_status_code: int, detail: str, unique_code: str = None,
                 detail_args: Dict = None, headers: Dict = None) -> None:
        """Throw a generic exception

        :param http_status_code: HTTP error code
        :type http_status_code: int
        :param detail: Human redable message of the error
        :type detail: str
        :param unique_code: Unique code to recognize the error,
        if not provided, a code is generated with filename and method name (that raised the exception), defaults to None
        If can also  be use for internationalisation (translating the detail message)
        :type unique_code: str, optional
        :param detail_args: if provided, it replace the arg in the detail message (between double bracket {{}}) with the corresponding dict value, defaults to None
        For example : detail = 'Hello {{name}}' and detail_args = {"name" : "Bob"}, the message that will be show will be 'Hello bob'
        This is useful for internationalisation
        :type detail_args: Dict, optional
        :param headers: if specific header need to be returned in the HTTP response, defaults to None
        :type headers: Dict, optional
        """
        super().__init__(status_code=http_status_code, detail=detail)
        self.detail = detail
        self.unique_code = unique_code
        self.detail_args = detail_args
        self.headers = headers
