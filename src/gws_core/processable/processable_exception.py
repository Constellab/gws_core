# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from __future__ import annotations

from typing import TYPE_CHECKING

from gws_core.core.exception.exception_handler import ExceptionHandler

from ..core.exception.exceptions.base_http_exception import BaseHTTPException

if TYPE_CHECKING:
    from .processable_model import ProcessableModel


class ProcessableRunException(Exception):
    """Generic exception to raised from another exception during the process run
    It show the original error and provided debug information about the process and experiment

    :param BadRequestException: [description]
    :type BadRequestException: [type]
    """

    unique_code: str
    exception_detail: str
    context: str

    original_exception: Exception
    processable_model: ProcessableModel

    def __init__(self, processable_model: ProcessableModel, exception_detail: str,
                 unique_code: str, exception: Exception) -> None:
        self.unique_code = unique_code
        self.exception_detail = exception_detail
        self.context = processable_model.get_instance_name_context()

        self.original_exception = exception
        self.processable_model = processable_model

    @staticmethod
    def from_exception(processable_model: ProcessableModel, exception: Exception) -> ProcessableRunException:
        # create from a know exception
        if isinstance(exception, BaseHTTPException):
            return ProcessableRunException(
                processable_model=processable_model, exception_detail=exception.get_detail_with_args(),
                unique_code=exception.unique_code, exception=exception)
        # create from a unknow exception
        else:
            return ProcessableRunException(processable_model=processable_model, exception_detail=str(exception),
                                           unique_code=ExceptionHandler._generate_unique_code_from_exception(),
                                           exception=exception)

    def update_context(self, context: str) -> None:
        self.context = context + ' > ' + self.context


# class ProcessableCheckBeforeException():
#     def __init__(self, processable_model: ProcessableModel, exception_detail: str, unique_code: str, exception: Exception) -> None:
#         self.original_exception = exception
#         self.processable_model = processable_model
#         detail_arg: Dict = {"error": exception_detail, **self.get_process_args()}
#         super().__init__(
#             GWSException.PROCESSABLE_RUN_EXCEPTION.value,
#             unique_code=unique_code,
#             detail_args=detail_arg)
