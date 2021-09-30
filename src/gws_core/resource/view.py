
from typing import Any

class View:
    
    _type: str
    _data: Any

    def __init__(self, type: str, data: Any):
        self._type = type
        self._data = data

    def to_dict(self, title: str=None, subtitle: str=None) -> dict:
        pass