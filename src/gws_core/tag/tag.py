
from typing import Dict, List

from pydantic.main import BaseModel

KEY_VALUE_SEPARATOR: str = ':'
TAGS_SEPARATOR = ','

# List of default tag with values
default_tags = {
    "status": ['SUCCESS', 'WARNING', 'ERROR'],
    "type": ['DATA', 'ARRAY', 'EXPERIMENT', 'JSON'],
    "name": []
}


class Tag(BaseModel):
    key: str
    value: str

    def __init__(self, key: str, value: str) -> None:
        super().__init__(key=key, value=value)

    def __str__(self) -> str:
        return self.key + ':' + self.value

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Tag):
            return False
        return (self is o) or (self.key == o.key and self.value == o.value)

    @staticmethod
    def from_string(tag_str: str) -> 'Tag':
        tag_info: List[str] = tag_str.split(KEY_VALUE_SEPARATOR)
        return Tag(tag_info[0], tag_info[1])

    def to_json(self) -> Dict:
        return {"key": self.key, "value": self.value}


class TagHelper():

    @classmethod
    def add_or_replace_tag(cls, tags_str: str, tag_key: str, tag_value: str) -> str:
        """Add of replace a tag key/value into a string
        """

        tags: List[Tag] = cls.tags_to_list(tags_str)

        if not tags:
            return str(Tag(tag_key, tag_value))

        same_key: List[Tag] = [x for x in tags if x.key == tag_key]

        if same_key:
            same_key[0].value = tag_value
        else:
            tags.append(Tag(tag_key, tag_value))

        return cls.tags_to_str(tags)

    @classmethod
    def tags_to_str(cls, tags: List[Tag]) -> str:
        if not tags:
            return ''
        return TAGS_SEPARATOR.join([str(tag) for tag in tags])

    @classmethod
    def tags_to_list(cls, tags: str) -> List[Tag]:
        if not tags:
            return []

        tags_list: List[Tag] = []

        for tag_str in tags.split(TAGS_SEPARATOR):
            tags_list.append(Tag.from_string(tag_str))
        return tags_list
