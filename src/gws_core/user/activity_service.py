# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from .activity import Activity
from .user import User


class ActivityService:

    @classmethod
    def add(cls, activity_type: str, object_type: str = None,
            object_id: str = None, user: User = None):
        Activity.add(
            activity_type=activity_type,
            object_type=object_type,
            object_id=object_id,
            user=user,
        )

    @classmethod
    def get_last_activity(cls) -> Optional[Activity]:
        return Activity.get_last_activity()
