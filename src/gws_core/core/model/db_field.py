import json
from datetime import date, datetime, timezone
from email.headerregistry import DateHeader

import pytz
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
