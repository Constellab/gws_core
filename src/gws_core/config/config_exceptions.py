
from typing import List

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
                         detail_args={"config_names": self.get_missing_params_text()})

    def get_missing_params_text(self) -> str:
        return ",".join(self.missing_params)
