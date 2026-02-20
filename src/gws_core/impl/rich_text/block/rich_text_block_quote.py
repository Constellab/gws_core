from gws_core.impl.rich_text.block.rich_text_block import (
    RichTextBlockDataBase,
    RichTextBlockTypeStandard,
)
from gws_core.impl.rich_text.block.rich_text_block_decorator import rich_text_block_decorator


@rich_text_block_decorator(RichTextBlockTypeStandard.QUOTE.value)
class RichTextBlockQuote(RichTextBlockDataBase):
    """Object representing a quote block in a rich text"""

    text: str
    caption: str | None = None

    def to_markdown(self) -> str:
        """Convert the quote to markdown

        :return: the markdown representation of the quote
        :rtype: str
        """
        markdown = f"> {self.text}"
        if self.caption:
            markdown += f"\n> — {self.caption}"
        return markdown
