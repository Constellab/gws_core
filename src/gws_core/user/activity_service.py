

from .activity import Activity
from .user import User


class ActivityService:

    # todo check le '*'
    @classmethod
    def add(self, activity_type: str, *, object_type=None, object_id=None, user: User = None):
        Activity.add(
            activity_type=activity_type,
            object_type=object_type,
            object_id=object_id,
            user=user,
        )
