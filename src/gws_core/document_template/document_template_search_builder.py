

from gws_core.core.classes.search_builder import SearchBuilder
from gws_core.document_template.document_template import DocumentTemplate


class NoteTemplateSearchBuilder(SearchBuilder):
    def __init__(self) -> None:
        super().__init__(DocumentTemplate, default_orders=[DocumentTemplate.last_modified_at.desc()])
