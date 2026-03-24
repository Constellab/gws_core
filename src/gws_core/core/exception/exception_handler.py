import uuid

from fastapi import status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.exceptions import HTTPException
from starlette.requests import Request

from ..classes.cors_config import CorsConfig
from ..utils.logger import Logger
from ..utils.request_context import RequestContext
from ..utils.settings import Settings
from .exception_response import ExceptionResponse
from .exceptions.base_http_exception import BaseHTTPException

CODE_SEPARATOR = "."


class ExceptionHandler:
    """Class to handle exceptions and return a formatted object to the front"""

    @classmethod
    def handle_request_validation_error(cls, exc: RequestValidationError):
        """
        Handle a RequestValidationError exception (error 422 Unprocessable Entity)
        It returns only the first message
        :param request:
        :param exc:
        :return:
        """

        # retrieve the error
        Logger.log_exception_stack_trace(exc)
        return ExceptionResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
            instance_id=cls.generate_instance_id(),
            request_id=RequestContext.get_request_id(),
        )

    @classmethod
    def handle_exception(cls, request: Request | None, exception: Exception) -> ExceptionResponse:
        if isinstance(exception, BaseHTTPException):
            return cls._handle_expected_exception(request, exception)
        elif isinstance(exception, HTTPException):
            return cls._handle_http_exception(request, exception)
        elif isinstance(exception, ValidationError):
            return cls._handle_validation_exception(request, exception)
        else:
            return cls._handle_unexcepted_exception(request, exception)

    @classmethod
    def _handle_expected_exception(
        cls, request: Request | None, exception: BaseHTTPException
    ) -> ExceptionResponse:
        """Handle the expected exception raised by the developper

        :param exception:
        :type exception: BaseHTTPException
        :return: [description]
        :rtype: ExceptionResponse
        """
        detail: str = exception.get_detail_with_args()

        route_info: str = f" - Route: {request.url}" if request is not None else ""

        Logger.info(
            f"Handle exception - {route_info} - {detail} - Instance id : {exception.instance_id}"
        )
        if Logger.is_debug_level():
            Logger.log_exception_stack_trace(exception)

        return ExceptionResponse(
            status_code=exception.status_code,
            detail=detail,
            instance_id=exception.instance_id,
            code=exception.unique_code,
            show_as=exception.show_as,
            headers=exception.headers,
            request_id=RequestContext.get_request_id(),
        )

    @classmethod
    def _handle_http_exception(
        cls, request: Request | None, exception: HTTPException
    ) -> ExceptionResponse:
        """Handle the HTTP scarlett exceptions

        :param exception: scarlett exception
        :type exception: HTTPException
        :return: [description]
        :rtype: ExceptionResponse
        """
        instance_id: str = cls.generate_instance_id()

        route_info: str = f" - Route: {request.url}" if request is not None else ""
        Logger.info(
            f"Handle HTTP exception - {route_info} - {exception.detail} - Instance id : {instance_id}"
        )

        return ExceptionResponse(
            status_code=exception.status_code,
            detail=exception.detail,
            instance_id=instance_id,
            request_id=RequestContext.get_request_id(),
        )

    @classmethod
    def _handle_validation_exception(
        cls, request: Request | None, exception: ValidationError
    ) -> ExceptionResponse:
        """Handle the validation exception (error 422) it logs the stack trace and return a formated object

        Arguments:
            request {Request} -- [description]
            exception {ValidationError} -- [description]

        Returns:
            ExceptionResponse -- [description]
        """

        Logger.log_exception_stack_trace(exception)

        instance_id: str = cls.generate_instance_id()

        # Log short information with instance id (the stack trace is automatically printed)
        route_info: str = f" - Route: {request.url}" if request is not None else ""
        Logger.error(
            f"Validation exception - {route_info} - {str(exception)} - Instance id : {instance_id}"
        )

        # return only the first error
        errors = exception.errors()
        detail = "Validation error : "
        if errors:
            first_error = errors[0]
            detail += (
                f"{first_error['msg']} - Field : {'.'.join([str(x) for x in first_error['loc']])}"
            )
        else:
            detail += str(exception)

        return ExceptionResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            instance_id=instance_id,
            request_id=RequestContext.get_request_id(),
        )

    @classmethod
    def _handle_unexcepted_exception(
        cls, request: Request | None, exception: Exception
    ) -> ExceptionResponse:
        """Handle the unexcepted exception (error 500) it logs the stack trace and return a formated object

        Arguments:
            request {Request} -- [description]
            exception {Exception} -- [description]

        Returns:
            ExceptionResponse -- [description]
        """

        instance_id: str = cls.generate_instance_id()

        # Log short information with instance id (the stack trace is automatically printed)
        route_info: str = f" - Route: {request.url}" if request is not None else ""
        Logger.error(
            f"Unexcepted exception - {route_info} - {str(exception)}",
            instance_id=instance_id,
            exception=exception,
        )

        # In prod mode, hide the exception detail to avoid leaking internal information
        detail = "Internal server error" if Settings.is_prod_mode() else str(exception)

        response: ExceptionResponse = ExceptionResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            instance_id=instance_id,
            request_id=RequestContext.get_request_id(),
        )

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
    def generate_instance_id(cls) -> str:
        return str(uuid.uuid4())
