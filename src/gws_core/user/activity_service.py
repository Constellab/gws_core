

from .activity import Activity
from .current_user_service import CurrentUserService


class ActivityService:

    # todo check l'*
    @classmethod
    def add(self, activity_type: str, *, object_type=None, object_uri=None):
        Activity.add(
            activity_type=activity_type,
            object_type=object_type,
            object_uri=object_uri,
            user=CurrentUserService.get_current_user(),
        )
