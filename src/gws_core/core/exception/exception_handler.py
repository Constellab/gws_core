# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
import os
import uuid
from typing import List

from fastapi import status
from starlette.exceptions import HTTPException
from starlette.requests import Request

from ..classes.cors_config import CorsConfig
from ..utils.logger import Logger
from ..utils.utils import Utils
from .exception_response import ExceptionResponse
from .exceptions.base_http_exception import BaseHTTPException

CODE_SEPARATOR = '.'


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

        unique_code: str

        if exception.unique_code is not None:
            # If the unique code is provided, append the brick name to make it unique
            unique_code = cls.get_unique_code_for_brick(exception.unique_code)
        else:
            # otherwise, generate an unique code
            unique_code = cls.generate_unique_code_from_exception()

        route_info: str = f" - Route: {request.url}" if request is not None else ""

        Logger.info(
            f"Handle exception - {unique_code}{route_info} - {detail} - Instance id : {exception.instance_id}")

        return ExceptionResponse(status_code=exception.status_code, code=unique_code,
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
        instance_id: str = cls.generate_instance_id()
        code = cls.generate_unique_code_from_exception()

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

        Logger.log_exception_stack_trace(exception)

        instance_id: str = cls.generate_instance_id()
        code = cls.generate_unique_code_from_exception()

        # Log short information with instance id (the stack trace is automatically printed)
        route_info: str = f" - Route: {request.url}" if request is not None else ""
        Logger.error(
            f"Unexcepted exception - {code}{route_info} - {str(exception)} - Instance id : {instance_id}")

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

    @classmethod
    def generate_unique_code_from_exception(cls) -> str:
        """Generate a unique exception code from the stack trace

        :return: BRICK_NAME.FILE_NAME.METHOD_NAME
        :rtype: str
        """
        trace: List = inspect.trace()
        if not trace:
            return ""

        frame_info: inspect.FrameInfo = trace[-1]

        if frame_info is None:
            return ""

        code = os.path.split(
            frame_info.filename)[-1] + CODE_SEPARATOR + frame_info.function

        return cls.get_unique_code_for_brick(code)

    @classmethod
    def get_unique_code_for_brick(cls, code: str) -> str:
        """Convert the code to a unique code by adding the brick name before the code

        :param code: exception code
        :type code: str
        :return: exception unique code
        :rtype: str
        """
        return cls._get_brick_name() + CODE_SEPARATOR + code

    @classmethod
    def _get_brick_name(cls) -> str:
        """Retrieve the brick name of the raised exception from the full filename
        of the trace

        :return: brick name
        :rtype: str
        """
        trace: List = inspect.trace()
        if not trace:
            return ""

        frame_info: inspect.FrameInfo = trace[-1]

        try:
            return Utils.get_brick_name(frame_info[0])
        except Exception as err:
            Logger.error('Error when getting the brick of the exception')
            Logger.log_exception_stack_trace(err)
            return ""

    @classmethod
    def unique_code_separator(cls) -> str:
        return CODE_SEPARATOR

    @classmethod
    def generate_instance_id(cls) -> str:
        return str(uuid.uuid4())
