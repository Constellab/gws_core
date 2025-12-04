from gws_core.core.classes.search_builder import SearchBuilder
from gws_core.note_template.note_template import NoteTemplate


class NoteTemplateSearchBuilder(SearchBuilder):
    def __init__(self) -> None:
        super().__init__(NoteTemplate, default_orders=[NoteTemplate.last_modified_at.desc()])
