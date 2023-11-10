# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core.tag.entity_tag import EntityTagType
from gws_core.tag.entity_with_tag_search_builder import \
    EntityWithTagSearchBuilder

from .protocol_template import ProtocolTemplate


class ProtocolTemplateSearchBuilder(EntityWithTagSearchBuilder):

    def __init__(self) -> None:
        super().__init__(ProtocolTemplate, EntityTagType.PROTOCOL_TEMPLATE,
                         default_orders=[ProtocolTemplate.last_modified_at.desc()])
