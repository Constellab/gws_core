

from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.tag.entity_with_tag_search_builder import \
    EntityWithTagSearchBuilder

from .scenario_template import ScenarioTemplate


class ScenarioTemplateSearchBuilder(EntityWithTagSearchBuilder):

    def __init__(self) -> None:
        super().__init__(ScenarioTemplate, EntityType.SCENARIO_TEMPLATE,
                         default_orders=[ScenarioTemplate.last_modified_at.desc()])
