from datetime import datetime, timedelta
from typing import Optional, final

from peewee import CharField, ForeignKeyField

from gws_core.core.classes.enum_field import EnumField
from gws_core.user.activity.activity_dto import ActivityDTO, ActivityObjectType, ActivityType

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

    # For add of update activity, if the last activity or same type is less than ACTIVITY_MERGE_MAX_TIME seconds,
    # the activity will be updated
    ACTIVITY_MERGE_MAX_TIME = 60 * 5

    @classmethod
    def add(
        cls,
        activity_type: ActivityType,
        object_type: ActivityObjectType,
        object_id: str,
        user: User = None,
    ) -> "Activity":
        if user is None:
            user = CurrentUserService.get_and_check_current_user()
        activity = Activity(
            user=user, activity_type=activity_type, object_type=object_type, object_id=object_id
        )
        return activity.save()

    @classmethod
    def get_last_activity(cls) -> "Activity":
        return Activity.select().order_by(Activity.last_modified_at.desc()).first()

    @classmethod
    def add_or_update(
        cls,
        activity_type: ActivityType,
        object_type: ActivityObjectType,
        object_id: str,
        user: User = None,
    ) -> "Activity":
        max_date = datetime.now() - timedelta(seconds=Activity.ACTIVITY_MERGE_MAX_TIME)

        same_activity = Activity.get_last_of_type(
            activity_type=activity_type,
            object_type=object_type,
            object_id=object_id,
            max_date=max_date,
            user=user,
        )

        if same_activity is not None:
            same_activity.last_modified_at = datetime.now()
            return same_activity.save()
        else:
            return cls.add(activity_type, object_type, object_id, user)

    @classmethod
    def get_last_of_type(
        cls,
        activity_type: ActivityType,
        object_type: ActivityObjectType,
        object_id: str,
        max_date: datetime,
        user: User = None,
    ) -> Optional["Activity"]:
        """Method to check if an activity exists for a given type and object
        and is more recent than a given date

        :return: _description_
        :rtype: _type_
        """
        if user is None:
            user = CurrentUserService.get_and_check_current_user()
        return (
            Activity.select()
            .where(
                (Activity.activity_type == activity_type)
                & (Activity.user == user)
                & (Activity.object_type == object_type)
                & (Activity.object_id == object_id)
                & (Activity.last_modified_at > max_date)
            )
            .order_by(Activity.created_at.desc())
            .first()
        )

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

    class Meta:
        table_name = "gws_user_activity"
        is_table = True
