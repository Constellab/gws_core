from gws_core.note.note import Note
from gws_core.tag.entity_with_tag_search_builder import EntityWithTagSearchBuilder
from gws_core.tag.tag_entity_type import TagEntityType


class NoteSearchBuilder(EntityWithTagSearchBuilder):
    def __init__(self) -> None:
        super().__init__(Note, TagEntityType.NOTE, default_orders=[Note.last_modified_at.desc()])

    def add_title_filter(self, title: str) -> None:
        """Add a filter to search for notes with titles containing the given substring.

        :param title: Substring to search for in note titles.
        :type title: str
        """
        like_pattern = f"%{title}%"
        self.add_expression(Note.title.ilike(like_pattern))
