from gws_core.impl.rich_text.block.rich_text_block import (
    RichTextBlockDataBase,
    RichTextBlockTypeStandard,
)
from gws_core.impl.rich_text.block.rich_text_block_decorator import rich_text_block_decorator


@rich_text_block_decorator(RichTextBlockTypeStandard.IFRAME.value)
class RichTextBlockIframe(RichTextBlockDataBase):
    iframeHeight: int
    url: str

    def to_markdown(self) -> str:
        """Convert the iframe to markdown

        :return: the markdown representation of the iframe
        :rtype: str
        """
        return f"<iframe src='{self.url}' height='{self.iframeHeight}'></iframe>"
