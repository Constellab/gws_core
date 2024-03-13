

from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.tag.entity_with_tag_search_builder import \
    EntityWithTagSearchBuilder

from .protocol_template import ProtocolTemplate


class ProtocolTemplateSearchBuilder(EntityWithTagSearchBuilder):

    def __init__(self) -> None:
        super().__init__(ProtocolTemplate, EntityType.PROTOCOL_TEMPLATE,
                         default_orders=[ProtocolTemplate.last_modified_at.desc()])
