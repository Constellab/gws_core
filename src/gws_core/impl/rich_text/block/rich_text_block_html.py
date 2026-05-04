from gws_core.impl.rich_text.block.rich_text_block import (
    RichTextBlockDataBase,
    RichTextBlockTypeStandard,
)
from gws_core.impl.rich_text.block.rich_text_block_decorator import rich_text_block_decorator


@rich_text_block_decorator(RichTextBlockTypeStandard.HTML.value)
class RichTextBlockHTML(RichTextBlockDataBase):
    html: str | None = None  # HTML content

    def to_markdown(self) -> str:
        """Convert the iframe to markdown

        :return: the markdown representation of the iframe
        :rtype: str
        """
        return self.html or ""
