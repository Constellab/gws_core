# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Optional

from peewee import ModelSelect

from gws_core.core.classes.paginator import Paginator
from gws_core.core.classes.search_builder import SearchBuilder, SearchParams

from ..user import User
from .activity import Activity, ActivityObjectType, ActivityType
from .activity_search_builder import ActivitySearchBuilder


class ActivityService:

    @classmethod
    def add(cls, activity_type: ActivityType, object_type: ActivityObjectType,
            object_id: str, user: User = None):
        Activity.add(
            activity_type=activity_type,
            object_type=object_type,
            object_id=object_id,
            user=user,
        )

    @classmethod
    def get_last_activity(cls) -> Optional[Activity]:
        return Activity.get_last_activity()

    @classmethod
    def search(cls,
               search: SearchParams,
               page: int = 0,
               number_of_items_per_page: int = 20) -> Paginator[Activity]:

        search_builder: SearchBuilder = ActivitySearchBuilder()

        model_select: ModelSelect = search_builder.build_search(search)
        return Paginator(
            model_select, page=page, nb_of_items_per_page=number_of_items_per_page)