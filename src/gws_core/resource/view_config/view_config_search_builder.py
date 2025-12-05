
from peewee import Expression

from gws_core.core.classes.search_builder import SearchFilterCriteria, SearchOperator
from gws_core.resource.view.view_types import ViewType
from gws_core.scenario.scenario import Scenario
from gws_core.tag.entity_with_tag_search_builder import EntityWithTagSearchBuilder
from gws_core.tag.tag_entity_type import TagEntityType

from .view_config import ViewConfig


class ViewConfigSearchBuilder(EntityWithTagSearchBuilder):
    """Search build for the view cofnig

    :param SearchBuilder: [description]
    :type SearchBuilder: [type]
    """

    def __init__(self) -> None:
        super().__init__(
            ViewConfig, TagEntityType.VIEW, default_orders=[ViewConfig.last_modified_at.desc()]
        )

    def convert_filter_to_expression(self, filter_: SearchFilterCriteria) -> Expression:
        if filter_.key == "include_not_favorite":
            return None
        elif filter_.key == "folder":
            # Handle the folder filters, get all scenario of this folder and filter by scenario
            scenarios: list[Scenario] = list(
                Scenario.select().where(Scenario.folder.in_(filter_.value))
            )
            return ViewConfig.scenario.in_(scenarios)
        elif filter_.key == "view_type":
            # consider table and tabular the same
            if ViewType.TABLE.value == filter_.value:
                filter_.value = [ViewType.TABLE.value, ViewType.TABULAR.value]
                filter_.operator = SearchOperator.IN
        return super().convert_filter_to_expression(filter_)
