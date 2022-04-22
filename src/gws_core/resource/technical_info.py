# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Dict, List

from .r_field import JsonableObject


class TechnicalInfo:
    key: str
    value: str

    def __init__(self, key: str, value: str) -> None:
        self.key = key
        self.value = value

    def to_json(self) -> Dict[str, str]:
        return {
            "key": self.key,
            "value": self.value
        }

    @classmethod
    def from_json(cls, json_data: Dict[str, str]) -> 'TechnicalInfo':
        return TechnicalInfo(key=json_data["key"], value=json_data["value"])


class TechnicalInfoDict(JsonableObject):
    _technical_info: Dict[str, TechnicalInfo]

    def __init__(self):
        self._technical_info = {}

    def add(self, technical_info: TechnicalInfo):
        if technical_info.key in self._technical_info:
            raise ValueError(f"Technical information key {technical_info.key} already exists")
        self._technical_info[technical_info.key] = technical_info

    def get(self, key: str) -> TechnicalInfo:
        if key not in self._technical_info:
            raise ValueError(f"Technical information key {key} does not exist")
        return self._technical_info[key]

    def to_json(self) -> List[Dict[str, str]]:
        return [technical_info.to_json() for technical_info in self._technical_info.values()]

    def is_empty(self) -> bool:
        return len(self._technical_info) == 0

    @classmethod
    def from_json(cls, json_data: List[Dict[str, str]]) -> 'TechnicalInfoDict':
        technical_info_dict = TechnicalInfoDict()
        for technical_info_json in json_data:
            technical_info_dict.add(TechnicalInfo.from_json(technical_info_json))
        return technical_info_dict
