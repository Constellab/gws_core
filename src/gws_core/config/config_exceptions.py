# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, List

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.exception.gws_exceptions import GWSException


class MissingConfigsException(BadRequestException):
    """Exception raised when one or multiple mandatory config params were not provided
    """

    missing_params: List[str]

    def __init__(self, missing_params: List[str]) -> None:
        self.missing_params = missing_params
        super().__init__(detail=GWSException.MISSING_CONFIG_PARAMS.value,
                         unique_code=GWSException.MISSING_CONFIG_PARAMS.name,
                         detail_args={"param_names": self.get_missing_params_text()})

    def get_missing_params_text(self) -> str:
        return ",".join(self.missing_params)


class UnkownParamException(BadRequestException):
    """Exception raised when a param is not defined in a config
    """

    param_name: str

    def __init__(self, param_name: str) -> None:
        self.param_name = param_name
        super().__init__(detail=GWSException.UNKNOWN_CONFIG_PARAMS.value,
                         unique_code=GWSException.UNKNOWN_CONFIG_PARAMS.name,
                         detail_args={"param_name": self.param_name})


class InvalidParamValueException(BadRequestException):
    """Exception raised when the param value of a config is invalid
    """

    param_name: str
    param_value: Any
    error: str

    def __init__(self, param_name: str, param_value: Any, error: str) -> None:
        self.param_name = param_name
        self.param_value = param_value
        self.error = error
        super().__init__(detail=GWSException.INVALID_PARAM_VALUE.value,
                         unique_code=GWSException.INVALID_PARAM_VALUE.name,
                         detail_args={"param_name": param_name, "param_value": str(param_value), "error": error})
