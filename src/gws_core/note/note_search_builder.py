

from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.note.note import Note
from gws_core.tag.entity_with_tag_search_builder import \
    EntityWithTagSearchBuilder


class NoteSearchBuilder(EntityWithTagSearchBuilder):
    def __init__(self) -> None:
        super().__init__(Note, EntityType.NOTE,
                         default_orders=[Note.last_modified_at.desc()])
