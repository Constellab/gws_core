

from gws_core.core.classes.search_builder import SearchBuilder
from gws_core.user.activity.activity import Activity


class ActivitySearchBuilder(SearchBuilder):

    def __init__(self) -> None:
        super().__init__(Activity, default_orders=[Activity.last_modified_at.desc()])
