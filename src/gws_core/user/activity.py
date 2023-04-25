# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com
from typing import final

from peewee import CharField, ForeignKeyField

from ..core.model.model import Model
from .current_user_service import CurrentUserService
from .user import User


@final
class Activity(Model):
    """
    (User) Activity class
    """

    user: User = ForeignKeyField(User, null=False, index=True)
    activity_type = CharField(null=False, index=True)
    object_type = CharField(null=True, index=True)
    object_id = CharField(null=True, index=True)

    _table_name = "gws_user_activity"

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    SAVE = "SAVE"
    START = "START"
    STOP = "STOP"
    DELETE = "DELETE"
    ARCHIVE = "ARCHIVE"
    VALIDATE_EXPERIMENT = "VALIDATE_EXPERIMENT"
    HTTP_AUTHENTICATION = "HTTP_AUTHENTICATION"
    HTTP_UNAUTHENTICATION = "HTTP_UNAUTHENTICATION"
    CONSOLE_AUTHENTICATION = "CONSOLE_AUTHENTICATION"
    CONSOLE_UNAUTHENTICATION = "CONSOLE_UNAUTHENTICATION"

    def archive(self, archive: bool) -> None:
        """
        Deactivated method. Allways returns False.
        """

        return None

    @classmethod
    def add(cls, activity_type: str, object_type: str = None, object_id: str = None, user: User = None):
        if user is None:
            user = CurrentUserService.get_and_check_current_user()
        activity = Activity(
            user=user,
            activity_type=activity_type,
            object_type=object_type,
            object_id=object_id
        )
        activity.save()

    @classmethod
    def get_last_activity(cls) -> "Activity":
        return Activity.select().order_by(Activity.created_at.desc()).first()

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns JSON string or dictionnary representation of the model.

        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """

        _json = super().to_json(deep=deep, **kwargs)

        if self.user:
            _json["user"] = self.user.to_json()

        return _json
