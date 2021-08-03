

from .activity import Activity
from .user import User


class ActivityService:

    # todo check l'*
    @classmethod
    def add(self, activity_type: str, *, object_type=None, object_uri=None, user: User = None):
        Activity.add(
            activity_type=activity_type,
            object_type=object_type,
            object_uri=object_uri,
            user=user,
        )
