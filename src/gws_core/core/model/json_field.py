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

    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        if value is not None:
            return json.loads(value)
        return None
