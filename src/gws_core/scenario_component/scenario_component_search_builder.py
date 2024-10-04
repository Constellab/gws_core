

from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.tag.entity_with_tag_search_builder import \
    EntityWithTagSearchBuilder

from .scenario_component import ScenarioComponent


class ScenarioComponentSearchBuilder(EntityWithTagSearchBuilder):

    def __init__(self) -> None:
        super().__init__(ScenarioComponent, EntityType.SCENARIO_COMPONENT,
                         default_orders=[ScenarioComponent.last_modified_at.desc()])
