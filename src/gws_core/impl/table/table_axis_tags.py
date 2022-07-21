# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from copy import deepcopy
from typing import Dict, List

from gws_core.resource.r_field import SerializableObject
from gws_core.tag.tag_helper import TagHelper


class TableAxisTags(SerializableObject):

    _tags: List[Dict[str, str]] = None

    def __init__(self, tags: List[Dict[str, str]] = None):
        super().__init__()

        if tags is None:
            self._tags = []
        else:
            self.set_all_tags(tags)

    def insert_new_empty_tags(self, index: int = None):
        """
        Add a new empty tags dict.
        If index is None, the new tags will be added at the end of the list.
        """
        if index is None:
            self._tags.append({})
        else:
            self._tags.insert(index, {})

    def add_tag_at(self, index: int, key: str, value: str):
        self._check_tag_index(index)
        self._check_tag(key, value)

        self._tags[index][key] = value

    def set_tags_at(self, index: int, tags: Dict[str, str]):
        """ Set the tags at the given index (override previous tags)"""
        self._check_tag_index(index)
        self._check_tags(tags)

        self._tags[index] = tags

    def set_all_tags(self, tags: List[Dict[str, str]]):
        if not isinstance(tags, list):
            raise Exception("The tags must be a list")

        try:
            self._tags = [{str(k): str(v) for k, v in t.items()} for t in tags]
        except Exception as err:
            raise Exception(f"The tags are not valid. Please check. Error message: {err}")

    def get_tags_between(self, from_index: int = None, to_index: int = None,
                         none_if_empty: bool = False) -> List[Dict[str, str]]:
        """Get the tags between the given indexes. It includes the to_index """
        if none_if_empty and self.all_tag_are_empty():
            return None

        if from_index is not None and to_index is not None:
            self._check_tag_index(from_index)
            self._check_tag_index(to_index)
            return deepcopy(self._tags[from_index:to_index + 1])

        return self.get_all_tags()

    def get_tags_at(self, index: int) -> Dict[str, str]:
        self._check_tag_index(index)
        return deepcopy(self._tags[index])

    def get_tags_at_indexes(self, indexes: List[int]) -> List[Dict[str, str]]:
        return deepcopy([self._tags[i] for i in indexes])

    def get_all_tags(self) -> List[Dict[str, str]]:
        return deepcopy(self._tags)

    def all_tag_are_empty(self) -> bool:
        return all(len(t) == 0 for t in self._tags)

    @property
    def size(self) -> int:
        return len(self._tags)

    def get_available_tags(self) -> Dict[str, List[str]]:
        """Get the complete list of tags with list of values for each
        """
        return TagHelper.get_distinct_values(self._tags)

    def _check_tag_index(self, index: int) -> None:
        if not isinstance(index, int):
            raise Exception("The index must be an integer")
        if index < 0 or index >= self.size:
            raise Exception("The index is out of range")

    def _check_tags(self, tags: Dict[str, str]) -> None:
        if not isinstance(tags, dict):
            raise Exception("The tags must be a dict")

        for k, v in tags.items():
            self._check_tag(k, v)

    def _check_tag(self, key: str, value: str) -> None:
        if not isinstance(key, str):
            raise Exception("The tag key must be a string")
        if not isinstance(value, str):
            raise Exception("The tag value must be a string")

    def serialize(self) -> Dict:
        return {"tags": self._tags}

    @classmethod
    def deserialize(cls, data: Dict) -> 'TableAxisTags':
        if data is None or data.get("tags") is None:
            return TableAxisTags([])

        return TableAxisTags(data["tags"])
