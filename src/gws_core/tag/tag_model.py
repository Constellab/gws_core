

from typing import List, Optional

from peewee import CharField

from ..core.model.model import Model


class TagModel(Model):
    TAG_VALUES_SEPARATOR = ','

    key = CharField(null=False, unique=True)

    _table_name = "gws_tag"

    @property
    def values(self) -> List[str]:
        if 'values' not in self.data:
            return []

        tag_values: str = self.data['values']

        if not tag_values:
            return []

        return tag_values.split(self.TAG_VALUES_SEPARATOR)

    def has_value(self, value: str) -> bool:
        return value in self.values

    def add_value(self, value: str) -> None:
        """Add the value if not present

        :return: [description]
        :rtype: [type]
        """
        if not value:
            return
        value = value.lower()
        if self.has_value(value):
            return

        values = self.values
        values.append(value)
        self.data['values'] = self.TAG_VALUES_SEPARATOR.join(values)

    @classmethod
    def create(cls, key: str, values: List[str] = []) -> 'TagModel':
        """create a new empty tag

        :param key: [description]
        :type key: str
        :return: [description]
        :rtype: Tag
        """
        tag = TagModel()
        tag.key = key.lower()
        tag.data = {'values': cls.TAG_VALUES_SEPARATOR.join(values)}
        return tag

    @classmethod
    def find_by_key(cls, key: str) -> Optional['TagModel']:
        try:
            return cls.get(cls.key == key)
        except:
            return None

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        json_ = super().to_json(deep=deep, **kwargs)
        json_['values'] = self.values
        return json_

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        return None
