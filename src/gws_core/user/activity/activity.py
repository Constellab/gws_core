# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from enum import Enum
from typing import final

from peewee import CharField, ForeignKeyField

from gws_core.core.classes.enum_field import EnumField

from ...core.model.model import Model
from ..current_user_service import CurrentUserService
from ..user import User


class ActivityType(Enum):
    CREATE = "CREATE"
    DELETE = "DELETE"
    ARCHIVE = "ARCHIVE"
    UNARCHIVE = "UNARCHIVE"
    VALIDATE = "VALIDATE"
    HTTP_AUTHENTICATION = "HTTP_AUTHENTICATION"
    RUN_EXPERIMENT = "RUN_EXPERIMENT"
    RUN_PROCESS = "RUN_PROCESS"
    STOP_EXPERIMENT = "STOP_EXPERIMENT"
    LAB_START = "LAB_START"


class ActivityObjectType(Enum):
    EXPERIMENT = "EXPERIMENT"
    PROCESS = "PROCESS"
    USER = "USER"
    REPORT = "REPORT"


@final
class Activity(Model):
    """
    (User) Activity class
    """

    user: User = ForeignKeyField(User, null=False)
    activity_type = EnumField(choices=ActivityType, null=False)
    object_type = EnumField(choices=ActivityObjectType, null=False)
    object_id = CharField(null=False, max_length=36)

    _table_name = "gws_user_activity"

    def archive(self, archive: bool) -> None:
        """
        Deactivated method. Allways returns False.
        """

        return None

    @classmethod
    def add(cls, activity_type: ActivityType, object_type: ActivityObjectType,
            object_id: str, user: User = None):
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
