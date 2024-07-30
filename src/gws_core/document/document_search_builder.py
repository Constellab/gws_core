

from typing import Type

from gws_core.document.document import Document
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.tag.entity_with_tag_search_builder import \
    EntityWithTagSearchBuilder


class DocumentSearchBuilder(EntityWithTagSearchBuilder):
    def __init__(self, document_type: Type[Document],
                 entity_type: EntityType) -> None:
        super().__init__(document_type, entity_type,
                         default_orders=[document_type.last_modified_at.desc()])
