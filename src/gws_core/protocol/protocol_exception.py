
from __future__ import annotations

from typing import Dict, Literal

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.exception.exceptions.base_http_exception import BaseHTTPException
from ..core.exception.gws_exceptions import GWSException


class ProtocolBuildException(BadRequestException):

    original_exception: Exception
    original_detail: str

    processable_type: Literal['Process', 'Protocol']
    instance_name_chain: str  # all processable instance name up to Main Protocol

    def __init__(
            self, processable_type: Literal['Process', 'Protocol'],
            instance_name: str,
            parent_instance_name: str,
            exception_detail: str,
            unique_code: str,
            exception: Exception) -> None:
        self.original_exception = exception
        self.original_detail = exception_detail
        self.processable_type = processable_type

        # Build the instance name chain
        self.instance_name_chain = self._get_instance_name_chain(
            parent_instance_name=parent_instance_name, instance_name_chain=instance_name)
        detail_arg: Dict = {"error": exception_detail, "instance_name": self.instance_name_chain}
        super().__init__(
            self._get_error_message(),
            unique_code=unique_code,
            detail_args=detail_arg)

    @staticmethod
    def from_exception(processable_type: Literal['Process', 'Protocol'],
                       instance_name: str, exception: Exception) -> ProtocolBuildException:
        # create from a know exception
        if isinstance(exception, BaseHTTPException):
            return ProtocolBuildException(
                processable_type=processable_type,
                instance_name=instance_name,
                parent_instance_name=None,
                exception_detail=exception.get_detail_with_args(),
                unique_code=exception.unique_code,
                exception=exception)
        # create from a unknow exception
        else:
            return ProtocolBuildException(
                processable_type=processable_type,
                instance_name=instance_name,
                parent_instance_name=None,
                exception_detail=str(exception),
                unique_code=GWSException.PROCESSABLE_RUN_EXCEPTION.name,
                exception=exception)

    # Build from a ProtocolBuildException to provide parent instance_name
    @staticmethod
    def from_build_exception(parent_instance_name: str, exception: ProtocolBuildException) -> ProtocolBuildException:
        return ProtocolBuildException(
            processable_type=exception.processable_type,
            instance_name=exception.instance_name_chain,
            parent_instance_name=parent_instance_name,
            exception_detail=exception.original_detail,
            unique_code=GWSException.PROCESSABLE_RUN_EXCEPTION.name,
            exception=exception.original_exception)

    # Build the instance name with the parent instance name
    def _get_instance_name_chain(self, parent_instance_name: str, instance_name_chain: str) -> str:
        if parent_instance_name is None and instance_name_chain is None:
            return "Main protocol"

        if parent_instance_name is None:
            return instance_name_chain

        return f"{parent_instance_name} > {instance_name_chain}"

    def _get_error_message(self) -> str:
        if self.processable_type == 'Protocol':
            return GWSException.PROTOCOL_BUILD_EXCEPTION.value
        else:
            return GWSException.PROCESS_BUILD_EXCEPTION.value
