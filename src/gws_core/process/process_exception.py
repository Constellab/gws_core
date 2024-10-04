

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.exception.exceptions.base_http_exception import BaseHTTPException
from ..core.exception.gws_exceptions import GWSException

if TYPE_CHECKING:
    from .process_model import ProcessModel


class ProcessRunException(BadRequestException):
    """Generic exception to raised from another exception during the process run
    It show the original error and provided debug information about the process and scenario

    :param BadRequestException: [description]
    :type BadRequestException: [type]
    """

    original_exception: Exception
    process_model: ProcessModel
    error_prefix: str

    def __init__(self, process_model: ProcessModel, exception_detail: str,
                 unique_code: str, error_prefix: str,
                 exception: Exception) -> None:
        super().__init__(
            detail=exception_detail,
            unique_code=unique_code)

        self.error_prefix = error_prefix
        self.original_exception = exception
        self.process_model = process_model

    @staticmethod
    def from_exception(process_model: ProcessModel, exception: Exception,
                       error_prefix: str = 'Error during task') -> ProcessRunException:

        unique_code: str

        # create from a know exception
        if isinstance(exception, BaseHTTPException):
            unique_code = exception.unique_code
        # create from a unknow exception
        else:
            unique_code = None

        return ProcessRunException(
            process_model=process_model, exception_detail=str(exception),
            unique_code=unique_code, error_prefix=error_prefix, exception=exception)

    def get_error_message(self, context: str = None) -> str:
        error = ""
        if context is not None:
            error = f"{self.error_prefix} '{context}' : "
        else:
            error = f"{self.error_prefix} : "
        error += f"{self.get_detail_with_args()}"
        return error


class CheckBeforeTaskStopException(BadRequestException):
    """Exception raised when the before task returned false and all the input of the task where provided

    :param BadRequestException: [description]
    :type BadRequestException: [type]
    :return: [description]
    :rtype: [type]
    """

    def __init__(self, message: str) -> None:
        super().__init__(detail=GWSException.TASK_CHECK_BEFORE_STOP.value,
                         unique_code=GWSException.TASK_CHECK_BEFORE_STOP.name,
                         detail_args={"message": message})
