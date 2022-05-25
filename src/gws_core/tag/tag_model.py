# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import List, Optional

from peewee import CharField, IntegerField

from ..core.model.model import Model


class TagModel(Model):
    TAG_VALUES_SEPARATOR = ','

    key = CharField(null=False, unique=True)
    order = IntegerField(default=0)

    _table_name = "gws_tag"

    @property
    def values(self) -> List[str]:
        if 'values' not in self.data:
            return []

        tag_values: List[List] = self.data['values']

        if not tag_values:
            return []

        return tag_values

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
        self.data['values'] = values

    def remove_value(self, value: str) -> None:
        """Remove the value if present

        :return: [description]
        :rtype: [type]
        """
        if not value or not self.has_value(value):
            return

        values = self.values
        if value in values:
            values.remove(value)
            self.data['values'] = values

    def update_value(self, old_value: str, new_value: str) -> None:
        """Update the value if present """
        self.remove_value(old_value)
        self.add_value(new_value)

    def set_values(self, values: List[str]) -> None:
        self.data['values'] = values

    def count_values(self) -> int:
        return len(self.values)

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
        tag.data = {'values': values}
        return tag

    @classmethod
    def find_by_key(cls, key: str) -> Optional['TagModel']:
        try:
            return cls.get(cls.key == key)
        except:
            return None

    @classmethod
    def get_highest_order(cls) -> int:
        tag_model: TagModel = cls.select().order_by(cls.order.desc()).first()

        if tag_model:
            return tag_model.order
        return -1

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        json_ = super().to_json(deep=deep, **kwargs)
        json_['values'] = self.values
        return json_

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        return None
