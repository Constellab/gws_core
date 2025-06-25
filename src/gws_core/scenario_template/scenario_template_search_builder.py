

from gws_core.tag.entity_with_tag_search_builder import \
    EntityWithTagSearchBuilder
from gws_core.tag.tag_entity_type import TagEntityType

from .scenario_template import ScenarioTemplate


class ScenarioTemplateSearchBuilder(EntityWithTagSearchBuilder):

    def __init__(self) -> None:
        super().__init__(ScenarioTemplate, TagEntityType.SCENARIO_TEMPLATE,
                         default_orders=[ScenarioTemplate.last_modified_at.desc()])
