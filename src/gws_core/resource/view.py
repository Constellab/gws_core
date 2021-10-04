
from typing import Any

class View:
    
    _type: str
    _data: Any

    def __init__(self, data: Any):
        self._data = self.check_and_clean_data(data)

    def check_and_clean_data(self, data):
        """ 
        Check the data and return.

        Must be overloaded to implement adhoc data checker
        """

        return data

    def to_dict(self, title: str=None, subtitle: str=None) -> dict:
        pass