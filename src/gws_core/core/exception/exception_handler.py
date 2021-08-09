# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
import os
import uuid
from typing import Dict

from fastapi import status
from gws_core.core.utils.utils import Utils
from starlette.exceptions import HTTPException

from ..utils.logger import Logger
from .exception_response import ExceptionResponse
from .exceptions.base_http_exception import BaseHTTPException

CODE_SEPARATOR = '.'


class ExceptionHandler():
    """Class to handle exceptions
    """

    @classmethod
    def handle_exception(cls, exception: Exception) -> ExceptionResponse:
        if isinstance(exception, BaseHTTPException):
            return cls._handle_expected_exception(exception)
        elif isinstance(exception, HTTPException):
            return cls._handle_http_exception(exception)
        else:
            return cls._handle_unexcepted_exception(exception)

    @classmethod
    def _handle_expected_exception(cls, exception: BaseHTTPException) -> ExceptionResponse:
        """Handle the expected exception raised by the developper

        :param exception:
        :type exception: BaseHTTPException
        :return: [description]
        :rtype: ExceptionResponse
        """
        instance_id: str = cls._get_instance_id()

        # generate a unique code if no code were specified
        unique_code: str = None
        if exception.unique_code is not None:
            unique_code = cls._get_unique_code_for_brick(exception.unique_code)
        else:
            unique_code = cls._generate_unique_code_from_exception()

        detail: str = None
        if exception.detail_args is not None and exception.detail is not None:
            detail = cls._replace_detail_args(
                exception.detail, exception.detail_args)
        else:
            detail = exception.detail

        Logger.info(
            f"Handle exception - {unique_code} - {exception.detail} - Instance id : {instance_id}")

        return ExceptionResponse(status_code=exception.status_code, code=unique_code,
                                 detail=detail,
                                 instance_id=instance_id, headers=exception.headers)

    @classmethod
    def _handle_http_exception(cls, exception: HTTPException) -> ExceptionResponse:
        """Handle the HTTP scarlett exceptions

        :param exception: scarlett exception
        :type exception: HTTPException
        :return: [description]
        :rtype: ExceptionResponse
        """
        instance_id: str = cls._get_instance_id()
        code = cls._generate_unique_code_from_exception()
        Logger.info(
            f"Handle HTTP exception - {code} - {exception.detail} - Instance id : {instance_id}")

        return ExceptionResponse(status_code=exception.status_code, code=code,
                                 detail=exception.detail,
                                 instance_id=instance_id)

    @classmethod
    def _handle_unexcepted_exception(cls, exception: Exception) -> ExceptionResponse:
        """Handle the unexcepted exception (error 500) it logs the stack trace and return a formated object

        Arguments:
            request {Request} -- [description]
            exception {Exception} -- [description]

        Returns:
            ExceptionResponse -- [description]
        """
        instance_id: str = cls._get_instance_id()
        code = cls._generate_unique_code_from_exception()

        # Log short information with instance id (the stack trace is automatically printed)
        Logger.error(
            f"Unexcepted exception - {code} - {str(exception)} - Instance id : {instance_id}")

        return ExceptionResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                 code=code,
                                 detail=str(exception),
                                 instance_id=instance_id)

    @classmethod
    def _generate_unique_code_from_exception(cls) -> str:
        """Generate a unique exception code from the stack trace

        :return: BRICK_NAME.FILE_NAME.METHOD_NAME
        :rtype: str
        """
        frame_info: inspect.FrameInfo = inspect.trace()[-1]

        if frame_info is None:
            return ""

        code = os.path.split(
            frame_info.filename)[-1] + CODE_SEPARATOR + frame_info.function

        return cls._get_unique_code_for_brick(code)

    @classmethod
    def _get_unique_code_for_brick(cls, code: str) -> str:
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
        frame_info: inspect.FrameInfo = inspect.trace()[-1]

        return Utils.get_brick_name(frame_info[0])

    @classmethod
    def _replace_detail_args(cls, detail: str, detail_args: Dict) -> str:
        """Replace the arguments in the exception message with dict corresponding values
        For example : detail = 'Hello {{name}}' and detail_args = {"name" : "Bob"}, the message that will be show will be 'Hello bob'
        """

        replaced_detail: str = detail
        for key in detail_args:
            replaced_detail = replaced_detail.replace(
                "{{" + key + "}}", str(detail_args[key]))

        return replaced_detail

    @classmethod
    def _get_instance_id(cls) -> str:
        return str(uuid.uuid4())
