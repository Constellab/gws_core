from gws_core.note_template.note_template import NoteTemplate
from gws_core.tag.entity_with_tag_search_builder import EntityWithTagSearchBuilder
from gws_core.tag.tag_entity_type import TagEntityType


class NoteTemplateSearchBuilder(EntityWithTagSearchBuilder[NoteTemplate]):
    def __init__(self) -> None:
        super().__init__(NoteTemplate, TagEntityType.NOTE_TEMPLATE, default_orders=[NoteTemplate.last_modified_at.desc()])
