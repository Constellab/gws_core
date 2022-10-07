# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import json
from abc import abstractmethod
from datetime import datetime
from typing import Type

from gws_core.core.utils.date_helper import DateHelper
from peewee import DateTimeField, TextField

# ####################################################################
#
# Custom JSONField
#
# ####################################################################


class JSONField(TextField):
    """
    Custom JSONField class
    """

    JSON_FIELD_TEXT_TYPE = "LONGTEXT"
    field_type = JSON_FIELD_TEXT_TYPE

    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        if value is not None:
            return json.loads(value)
        return None


class DateTimeUTC(DateTimeField):
    """
    Custom Datetime DB field to convert dae to UTC before saving it and return date as UTC
    when getting the DB
    """

    def db_value(self, value):
        datetime_: datetime = super().db_value(value)

        if datetime_ is None:
            return datetime_

        return DateHelper.convert_datetime_to_utc(datetime_)

    def python_value(self, value):
        datetime_: datetime = super().python_value(value)

        if datetime_ is None:
            return datetime_

        return DateHelper.convert_datetime_to_utc(datetime_)


class SerializableObject():
    """
    Object that can be serialized and deserialized
    """

    @abstractmethod
    def serialize(self) -> str:
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, value: str) -> 'SerializableObject':
        pass


class SerializableDBField(TextField):
    """
    Custom field for the DB that support serialization and deserialization.
    """

    JSON_FIELD_TEXT_TYPE = "LONGTEXT"
    field_type = JSON_FIELD_TEXT_TYPE

    object_type: Type[SerializableObject] = None

    def __init__(self, object_type: Type[SerializableObject], *args, **kwargs):
        self.object_type = object_type
        super().__init__(*args, **kwargs)

    def db_value(self, value: SerializableObject) -> str:
        if value is None:
            return None
        return value.serialize()

    def python_value(self, value: str) -> SerializableObject:
        return self.object_type.deserialize(value)
