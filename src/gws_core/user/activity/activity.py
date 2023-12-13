# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import final

from peewee import CharField, ForeignKeyField

from gws_core.core.classes.enum_field import EnumField
from gws_core.user.activity.activity_dto import (ActivityDTO,
                                                 ActivityObjectType,
                                                 ActivityType)

from ...core.model.model import Model
from ..current_user_service import CurrentUserService
from ..user import User


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

    def to_dto(self) -> ActivityDTO:
        return ActivityDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            user=self.user.to_dto(),
            activity_type=self.activity_type,
            object_type=self.object_type,
            object_id=self.object_id,
        )
