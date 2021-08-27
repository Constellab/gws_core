
from __future__ import annotations

from typing import TYPE_CHECKING, Dict

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.exception.exceptions.base_http_exception import BaseHTTPException
from ..core.exception.gws_exceptions import GWSException

if TYPE_CHECKING:
    from .process_model import ProcessableModel


class ProcessableRunException(BadRequestException):
    """Generic exception to raised from another exception during the process run
    It show the original error and provided debug information about the process and experiment

    :param BadRequestException: [description]
    :type BadRequestException: [type]
    """

    original_exception: Exception
    processable_model: ProcessableModel

    def __init__(self, processable_model: ProcessableModel, exception_detail: str, unique_code: str, exception: Exception) -> None:
        self.original_exception = exception
        self.processable_model = processable_model
        detail_arg: Dict = {"error": exception_detail, **self.get_process_args()}
        super().__init__(
            GWSException.PROCESS_RUN_EXCEPTION.value,
            unique_code=unique_code,
            detail_args=detail_arg)

    @staticmethod
    def from_exception(processable_model: ProcessableModel, exception: Exception) -> ProcessableRunException:
        # don't create a ProcessRunException if it already one
        if isinstance(exception, ProcessableRunException):
            return exception
        # create from a know exception
        elif isinstance(exception, BaseHTTPException):
            return ProcessableRunException(
                processable_model=processable_model, exception_detail=exception.get_detail_with_args(),
                unique_code=exception.unique_code, exception=exception)
        # create from a unknow exception
        else:
            return ProcessableRunException(processable_model=processable_model, exception_detail=str(exception),
                                           unique_code=GWSException.PROCESS_RUN_EXCEPTION.name, exception=exception)

    def get_process_args(self) -> Dict:
        return {
            # Process instance name
            "process": self.processable_model.instance_name if self.processable_model.instance_name else self.processable_model.uri,
            # Protocol instance name
            "protocol": self.processable_model.parent_protocol.instance_name if self.processable_model.parent_protocol else "No protocol",
            # Experiment uri
            "experiment": self.processable_model.experiment.uri if self.processable_model.experiment else "No experiment"
        }
