# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Dict

from fastapi import HTTPException

from ..exception_helper import ExceptionHelper


class BaseHTTPException(HTTPException):
    """
    Generic exception
    All the exception that extends this exceptions are considered a excepted exceptions and
    those are not logged in the console nor the logging file
    """

    detail: str
    unique_code: str
    detail_args: Dict
    headers: Dict
    instance_id: str

    def __init__(self, http_status_code: int, detail: str, unique_code: str = None,
                 detail_args: Dict = None, headers: Dict = None, from_exception: 'BaseHTTPException' = None) -> None:
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
        :param from_exception: if specified the http_status_code, unique_code, headers and instance_id are copied from this exception
                                Only the detail and detail agrs change
        :type from_exception: BaseHTTPException, optional
        """
        super().__init__(status_code=http_status_code, detail=detail)
        self.detail = detail
        self.detail_args = detail_args

        if from_exception is not None and isinstance(from_exception, BaseHTTPException):
            self.unique_code = from_exception.unique_code
            self.headers = from_exception.headers
            self.instance_id = from_exception.instance_id
        else:
            self.unique_code = self.generate_unique_code(unique_code)
            self.headers = headers

            self.instance_id = ExceptionHelper.generate_instance_id()

    def generate_unique_code(self, unique_code: str) -> str:
        if unique_code is not None:
            # If the unique code is provided, append the brick name to make it unique
            return ExceptionHelper.get_unique_code_for_brick(unique_code)
        else:
            # otherwise, generate an unique code
            return ExceptionHelper.generate_unique_code_from_exception()

    def get_detail_with_args(self) -> str:
        """Replace the arguments in the exception message with dict corresponding values
        For example : detail = 'Hello {{name}}' and detail_args = {"name" : "Bob"}, the message that will be show will be 'Hello bob'
        """

        replaced_detail: str = self.detail

        if self.detail_args:
            for key in self.detail_args:
                replaced_detail = replaced_detail.replace(
                    "{{" + key + "}}", str(self.detail_args[key]))

        return replaced_detail

    def __str__(self) -> str:
        return self.get_detail_with_args()
