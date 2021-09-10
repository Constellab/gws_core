# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

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
    It show the original error and provided debug information about the process and experiment

    :param BadRequestException: [description]
    :type BadRequestException: [type]
    """

    context: str

    original_exception: Exception
    process_model: ProcessModel

    def __init__(self, process_model: ProcessModel, exception_detail: str,
                 unique_code: str, exception: Exception) -> None:
        super().__init__(
            detail=exception_detail,
            unique_code=unique_code)

        self.context = None
        self.original_exception = exception
        self.process_model = process_model

    @staticmethod
    def from_exception(process_model: ProcessModel, exception: Exception,
                       error_prefix: str = None) -> ProcessRunException:

        prefix_text: str = f"{error_prefix} | " if error_prefix is not None else ""
        unique_code: str

        # create from a know exception
        if isinstance(exception, BaseHTTPException):
            unique_code = exception.unique_code
        # create from a unknow exception
        else:
            unique_code = None

        return ProcessRunException(
            process_model=process_model, exception_detail=prefix_text + str(exception),
            unique_code=unique_code, exception=exception)

    def update_context(self, context: str) -> None:
        if self.context is None:
            self.context = context
            return

        self.context = context + ' > ' + self.context


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
