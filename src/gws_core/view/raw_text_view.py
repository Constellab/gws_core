from typing import List, Union
from .view import View
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException

class RawTextView(View):

    _data: List[str]

    def __init__(self, data: List[str]):
        if not isinstance(data, list):
            raise BadRequestException("The data must be a list of text")
        super().__init__(type="raw-text-view", data=data)

    def to_dict(self) -> dict:
        # ToDo : anticipe les gros fichiers
        
        series = self._data
        return {
            "type": self._type,
            "series": series
        }