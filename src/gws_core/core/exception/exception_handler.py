# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from fastapi import status
from gws_core.core.exception.exception_helper import ExceptionHelper
from starlette.exceptions import HTTPException
from starlette.requests import Request

from ..classes.cors_config import CorsConfig
from ..utils.logger import Logger
from .exception_response import ExceptionResponse
from .exceptions.base_http_exception import BaseHTTPException


class ExceptionHandler():
    """Class to handle exceptions and return a formatted object to the front
    """

    @classmethod
    def handle_exception(cls, request: Request, exception: Exception) -> ExceptionResponse:
        if isinstance(exception, BaseHTTPException):
            return cls._handle_expected_exception(request, exception)
        elif isinstance(exception, HTTPException):
            return cls._handle_http_exception(request, exception)
        else:
            return cls._handle_unexcepted_exception(request, exception)

    @classmethod
    def _handle_expected_exception(cls, request: Request, exception: BaseHTTPException) -> ExceptionResponse:
        """Handle the expected exception raised by the developper

        :param exception:
        :type exception: BaseHTTPException
        :return: [description]
        :rtype: ExceptionResponse
        """
        detail: str = exception.get_detail_with_args()

        route_info: str = f" - Route: {request.url}" if request is not None else ""

        Logger.info(
            f"Handle exception - {exception.unique_code}{route_info} - {detail} - Instance id : {exception.instance_id}")

        return ExceptionResponse(status_code=exception.status_code, code=exception.unique_code,
                                 detail=detail,
                                 instance_id=exception.instance_id, headers=exception.headers)

    @ classmethod
    def _handle_http_exception(cls, request: Request, exception: HTTPException) -> ExceptionResponse:
        """Handle the HTTP scarlett exceptions

        :param exception: scarlett exception
        :type exception: HTTPException
        :return: [description]
        :rtype: ExceptionResponse
        """
        instance_id: str = ExceptionHelper.generate_instance_id()
        code = ExceptionHelper.generate_unique_code_from_exception()

        route_info: str = f" - Route: {request.url}" if request is not None else ""
        Logger.info(
            f"Handle HTTP exception - {code}{route_info} - {exception.detail} - Instance id : {instance_id}")

        return ExceptionResponse(status_code=exception.status_code, code=code,
                                 detail=exception.detail,
                                 instance_id=instance_id)

    @classmethod
    def _handle_unexcepted_exception(cls, request: Request, exception: Exception) -> ExceptionResponse:
        """Handle the unexcepted exception (error 500) it logs the stack trace and return a formated object

        Arguments:
            request {Request} -- [description]
            exception {Exception} -- [description]

        Returns:
            ExceptionResponse -- [description]
        """

        instance_id: str = ExceptionHelper.generate_instance_id()
        code = ExceptionHelper.generate_unique_code_from_exception()

        # Log short information with instance id (the stack trace is automatically printed)
        route_info: str = f" - Route: {request.url}" if request is not None else ""
        Logger.error(
            f"Unexcepted exception - {code}{route_info} - {str(exception)} - Instance id : {instance_id}")
        Logger.log_exception_stack_trace(exception)

        response: ExceptionResponse = ExceptionResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                                        code=code,
                                                        detail=str(exception),
                                                        instance_id=instance_id)

        if request is not None:

            # Since the CORSMiddleware is not executed when an unhandled server exception
            # occurs, we need to manually set the CORS headers ourselves if we want the FE
            # to receive a proper JSON 500, opposed to a CORS error.
            # Setting CORS headers on server errors is a bit of a philosophical topic of
            # discussion in many frameworks, and it is currently not handled in FastAPI.
            # See dotnet core for a recent discussion, where ultimately it was
            # decided to return CORS headers on server failures:
            # https://github.com/dotnet/aspnetcore/issues/2378
            CorsConfig.configure_response_cors(request, response)

        return response
