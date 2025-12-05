from __future__ import annotations

from typing import Literal

from ..core.exception.exceptions.bad_request_exception import BadRequestException
from ..core.exception.exceptions.base_http_exception import BaseHTTPException
from ..core.exception.gws_exceptions import GWSException


class ProtocolBuildException(BadRequestException):
    original_exception: Exception
    original_detail: str

    process_type: Literal["Task", "Protocol"]
    instance_name_chain: str  # all process instance name up to Main Protocol

    def __init__(
        self,
        process_type: Literal["Task", "Protocol"],
        instance_name: str,
        parent_instance_name: str,
        exception_detail: str,
        unique_code: str,
        exception: Exception,
    ) -> None:
        self.original_exception = exception
        self.original_detail = exception_detail
        self.process_type = process_type

        # Build the instance name chain
        self.instance_name_chain = self._get_instance_name_chain(
            parent_instance_name=parent_instance_name, instance_name_chain=instance_name
        )
        detail_arg: dict = {"error": exception_detail, "instance_name": self.instance_name_chain}
        super().__init__(self._get_error_message(), unique_code=unique_code, detail_args=detail_arg)

    @staticmethod
    def from_exception(
        process_type: Literal["Task", "Protocol"], instance_name: str, exception: Exception
    ) -> ProtocolBuildException:
        # create from a know exception
        if isinstance(exception, BaseHTTPException):
            return ProtocolBuildException(
                process_type=process_type,
                instance_name=instance_name,
                parent_instance_name=None,
                exception_detail=exception.get_detail_with_args(),
                unique_code=exception.unique_code,
                exception=exception,
            )
        # create from a unknow exception
        else:
            return ProtocolBuildException(
                process_type=process_type,
                instance_name=instance_name,
                parent_instance_name=None,
                exception_detail=str(exception),
                unique_code=GWSException.PROTOCOL_BUILD_EXCEPTION.name,
                exception=exception,
            )

    # Build from a ProtocolBuildException to provide parent instance_name
    @staticmethod
    def from_build_exception(
        parent_instance_name: str, exception: ProtocolBuildException
    ) -> ProtocolBuildException:
        return ProtocolBuildException(
            process_type=exception.process_type,
            instance_name=exception.instance_name_chain,
            parent_instance_name=parent_instance_name,
            exception_detail=exception.original_detail,
            unique_code=GWSException.PROTOCOL_BUILD_EXCEPTION.name,
            exception=exception.original_exception,
        )

    # Build the instance name with the parent instance name
    def _get_instance_name_chain(self, parent_instance_name: str, instance_name_chain: str) -> str:
        if parent_instance_name is None and instance_name_chain is None:
            return "Main protocol"

        if parent_instance_name is None:
            return instance_name_chain

        return f"{parent_instance_name} > {instance_name_chain}"

    def _get_error_message(
        self,
    ) -> str:
        if self.process_type == "Protocol":
            return GWSException.PROTOCOL_BUILD_EXCEPTION.value
        else:
            return GWSException.TASK_BUILD_EXCEPTION.value


class IOFaceConnectedToTheParentDeleteException(BadRequestException):
    def __init__(
        self,
        ioface_type: Literal["interface", "outerface"],
        ioface_name: str,
        parent_protocol_name: str,
    ) -> None:
        super().__init__(
            detail=GWSException.IOFACE_CONNECTED_TO_PARENT_DELETE_ERROR.value,
            unique_code=GWSException.IOFACE_CONNECTED_TO_PARENT_DELETE_ERROR.name,
            detail_args={
                "ioface_type": ioface_type,
                "ioface_name": ioface_name,
                "parent_protocol_name": parent_protocol_name,
            },
        )
