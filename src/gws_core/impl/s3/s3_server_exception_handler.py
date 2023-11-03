# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from fastapi.responses import Response
from starlette.exceptions import HTTPException
from starlette.requests import Request

from gws_core.core.utils.logger import Logger
from gws_core.core.utils.response_helper import ResponseHelper
from gws_core.impl.s3.s3_server_exception import S3ServerException


class S3ServerExceptionHandler():

    @classmethod
    def handle_exception(cls, request: Request, exc: Exception) -> Response:
        """
        Handle an exception

        :param request: the request
        :param exc: the exception
        :return: the response
        """
        if isinstance(exc, S3ServerException):
            return cls._handle_s3_server_error(request, exc)
        elif isinstance(exc, HTTPException):
            return cls._handle_s3_http_error(request, exc)
        else:
            return cls._handle_unexcepted_exception(request, exc)

    @classmethod
    def _handle_s3_server_error(cls, request: Request, exc: S3ServerException) -> Response:
        """
        Handle an S3ServerError exception

        :param request: the request
        :param exc: the exception
        :return: the response
        """
        route_info: str = f" - Route: {request.method} {request.url}" if request is not None else ""

        Logger.info(f"Handle s3 exception - {exc.code} {route_info} - {exc.message}")
        return ResponseHelper.create_xml_response(xml_text=exc.to_xml(), status_code=exc.status_code)

    @classmethod
    def _handle_s3_http_error(cls, request: Request, exc: HTTPException) -> Response:
        """
        Handle an S3ServerError exception

        :param request: the request
        :param exc: the exception
        :return: the response
        """
        route_info: str = f" - Route: {request.method} {request.url}" if request is not None else ""

        Logger.info(f"Handle s3 http exception - {exc.status_code} {route_info} - {exc.detail}")
        s3_error = S3ServerException.from_http_exception(exc)
        return ResponseHelper.create_xml_response(xml_text=s3_error.to_xml(), status_code=exc.status_code)

    @classmethod
    def _handle_unexcepted_exception(cls, request: Request, exception: Exception) -> Response:
        Logger.log_exception_stack_trace(exception)

        route_info: str = f" - Route: {request.method} {request.url}" if request is not None else ""
        Logger.error(f"Unexpected s3 exception - {route_info} - {str(exception)}")

        s3_error = S3ServerException.from_exception(exception)

        return ResponseHelper.create_xml_response(xml_text=s3_error.to_xml(), status_code=s3_error.status_code)
