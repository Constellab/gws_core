# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from datetime import datetime
from enum import Enum
from typing import List, Optional

from peewee import CharField, IntegerField

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.utils.date_helper import DateHelper
from gws_core.tag.tag import TagValueType

from ..core.model.model import Model


class EntityTagValueFormat(Enum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    DATETIME = "DATETIME"


class TagModel(Model):
    TAG_VALUES_SEPARATOR = ','

    key = CharField(null=False, unique=True)
    order = IntegerField(default=0)

    value_format: EntityTagValueFormat = EnumField(
        choices=EntityTagValueFormat, null=False, default=EntityTagValueFormat.STRING)

    _table_name = "gws_tag"

    @property
    def values(self) -> List[TagValueType]:
        if 'values' not in self.data:
            return []

        tag_values: List[str] = self.data['values']

        if not tag_values:
            return []

        return [self.convert_str_value_to_type(value) for value in tag_values]

    def has_value(self, value: TagValueType) -> bool:
        check_value = self.check_and_convert_value(value)
        return check_value in self.values

    def add_value(self, value: TagValueType) -> None:
        """Add the value if not present

        :return: [description]
        :rtype: [type]
        """
        if not value:
            return

        checked_value: TagValueType = self.check_and_convert_value(value)
        if self.has_value(checked_value):
            return

        if not self.data.get('values'):
            self.data['values'] = []

        # store the values as string
        self.data['values'].append(self.convert_value_to_str(checked_value))

    def remove_value(self, value: TagValueType) -> None:
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

    def update_value(self, old_value: TagValueType, new_value: TagValueType) -> None:
        """Update the value if present """
        self.remove_value(old_value)
        self.add_value(new_value)

    def set_values(self, values: List[TagValueType]) -> None:
        for value in values:
            self.add_value(value)

    def count_values(self) -> int:
        return len(self.values)

    ############################################## CLASS METHODS ##############################################

    @classmethod
    def register_tag(cls, tag_key: str, tag_value: TagValueType) -> 'TagModel':
        tag: TagModel = cls.find_by_key(tag_key)

        if tag is None:
            value_format: EntityTagValueFormat = EntityTagValueFormat.STRING
            if isinstance(tag_value, int):
                value_format = EntityTagValueFormat.INTEGER
            elif isinstance(tag_value, float):
                value_format = EntityTagValueFormat.FLOAT
            elif isinstance(tag_value, datetime):
                value_format = EntityTagValueFormat.DATETIME
            tag = cls._create_tag(tag_key, [tag_value], value_format)
        else:
            tag.add_value(tag_value)

        return tag.save()

    @classmethod
    def _create_tag(cls, key: str, values: List[TagValueType] = None,
                    value_format: EntityTagValueFormat = EntityTagValueFormat.STRING) -> 'TagModel':
        """create a new empty tag
        """
        if not values:
            values = []
        tag = TagModel()
        tag.key = key
        tag.value_format = value_format
        tag.order = TagModel.get_highest_order() + 1

        tag.set_values(values)
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

    def check_and_convert_value(self, value: TagValueType) -> TagValueType:
        if value is None:
            raise Exception("The tag value cannot be None")
        try:
            if self._check_value(value):
                return value

            return self.convert_str_value_to_type(value)
        except:
            raise Exception(f"Invalid value type for tag {self.key}, expected {self.value_format.value}")

    def _check_value(self, value: TagValueType) -> bool:
        if value is None:
            return False
        if self.value_format == EntityTagValueFormat.INTEGER:
            return isinstance(value, int)
        elif self.value_format == EntityTagValueFormat.FLOAT:
            return isinstance(value, float)
        elif self.value_format == EntityTagValueFormat.DATETIME:
            return isinstance(value, datetime)
        else:
            return isinstance(value, str)

    def convert_str_value_to_type(self, value: str) -> TagValueType:
        if self.value_format == EntityTagValueFormat.INTEGER:
            return int(value)
        elif self.value_format == EntityTagValueFormat.FLOAT:
            return float(value)
        elif self.value_format == EntityTagValueFormat.DATETIME:
            return DateHelper.from_iso_str(value)
        else:
            return value

    def convert_value_to_str(self, value: TagValueType) -> str:
        if self.value_format == EntityTagValueFormat.DATETIME:
            return DateHelper.to_iso_str(value)
        else:
            return str(value)
