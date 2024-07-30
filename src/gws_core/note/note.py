

from typing import final

from gws_core.document.document import Document
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextDTO


@final
class Note(Document):

    _table_name = 'gws_note'

    @classmethod
    def get_entity_type(cls) -> EntityType:
        return EntityType.NOTE

    @classmethod
    def get_default_content(cls) -> RichTextDTO:
        return RichText.create_rich_text_dto([])

    class Meta:
        table_name = 'gws_note'
