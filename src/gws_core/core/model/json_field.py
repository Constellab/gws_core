import json

from peewee import TextField

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
