# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json

from peewee import CharField, ForeignKeyField

from ..core.model.model import Model
from .user import User


class Activity(Model):
    """
    (User) Activity class
    """

    user = ForeignKeyField(User, null=False, index=True)
    activity_type = CharField(null=False, index=True)
    object_type = CharField(null=True, index=True)
    object_uri = CharField(null=True, index=True)

    _is_removable = False
    _table_name = "gws_user_activity"

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    SAVE = "SAVE"
    START = "START"
    STOP = "STOP"
    DELETE = "DELETE"
    ARCHIVE = "ARCHIVE"
    VALIDATE = "VALIDATE"
    HTTP_AUTHENTICATION = "HTTP_AUTHENTICATION"
    HTTP_UNAUTHENTICATION = "HTTP_UNAUTHENTICATION"
    CONSOLE_AUTHENTICATION = "CONSOLE_AUTHENTICATION"
    CONSOLE_UNAUTHENTICATION = "CONSOLE_UNAUTHENTICATION"

    def archive(self, tf: bool) -> bool:
        """
        Deactivated method. Allways returns False.
        """

        return False

    @classmethod
    def add(self, activity_type: str, *, object_type=None, object_uri=None, user=None):
        from .user_service import UserService
        if not user:
            user = UserService.get_current_user()
        activity = Activity(
            user=user,
            activity_type=activity_type,
            object_type=object_type,
            object_uri=object_uri
        )
        activity.save()

    # -- T --

    def to_json(self, *, stringify: bool = False, prettify: bool = False, **kwargs) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the model.

        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """

        _json = super().to_json(**kwargs)
        _json["user"] = {
            "uri": self.user.uri,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name
        }
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
