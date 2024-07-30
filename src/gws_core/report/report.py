

from typing import final

from gws_core.document.document import Document
from gws_core.entity_navigator.entity_navigator_type import EntityType
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import (
    RichTextDTO, RichTextParagraphHeaderLevel)


@final
class Report(Document):

    _table_name = 'gws_report'

    @classmethod
    def get_entity_type(cls) -> EntityType:
        return EntityType.REPORT

    @classmethod
    def get_default_content(cls) -> RichTextDTO:
        return RichText.create_rich_text_dto(  # type: ignore
            [RichText.create_header("0", "Introduction", RichTextParagraphHeaderLevel.HEADER_1),
             RichText.create_paragraph("1", ""),
             RichText.create_paragraph("2", ""),
             RichText.create_header("3", "Methods", RichTextParagraphHeaderLevel.HEADER_1),
             RichText.create_paragraph("4", ""),
             RichText.create_paragraph("5", ""),
             RichText.create_header("6", "Results", RichTextParagraphHeaderLevel.HEADER_1),
             RichText.create_paragraph("7", ""),
             RichText.create_paragraph("8", ""),
             RichText.create_header("9", "Conclusion", RichTextParagraphHeaderLevel.HEADER_1),
             RichText.create_paragraph("10", ""),
             RichText.create_paragraph("11", ""),
             RichText.create_header("12", "References", RichTextParagraphHeaderLevel.HEADER_1),
             RichText.create_paragraph("13", "")
             ])

    class Meta:
        table_name = 'gws_report'
