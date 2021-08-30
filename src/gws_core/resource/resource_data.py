import copy
from typing import Dict, TypeVar

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException

ResourceDict = TypeVar('ResourceDict')


class ResourceData(Dict[str, ResourceDict]):

    def __init__(self, data: Dict[str, ResourceDict] = None):
        super().__init__()
        if data is None:
            return

        self.set_values(data)

    def set_values(self, data: Dict[str, ResourceDict]) -> None:
        if not isinstance(data, dict):
            raise BadRequestException(f"Can't instantiate ResourceData with data {str(data)} because it is not a dict")

        for key, value in data.items():
            self[key] = value

    def is_empty(self) -> bool:
        return len(self) == 0

    # -- T --
    def to_json(self) -> dict:
        return self

    # -- T --
    def clone(self) -> 'ResourceData':
        return ResourceData(copy.deepcopy(self))
