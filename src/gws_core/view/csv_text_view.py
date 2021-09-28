from typing import List
from pandas import DataFrame
from .view import View
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException

class CSVTextView(View):

    _data: List[DataFrame]

    def __init__(self, data: List[DataFrame]):
        if not isinstance(data, list):
            raise BadRequestException("The data must be a list of DataFrame")
        super().__init__(type="csv-text-view", data=data)

    def to_dict(self) -> dict:
        # ToDo : anticipe les gros fichiers
        
        series = []
        for df in self._data:
            series.append( df.to_dict() )

        return {
            "type": self._type,
            "series": series
        }