

from gws_core.impl.rich_text.block.rich_text_block import (
    RichTextBlockDataBase, RichTextBlockType)


class RichTextBlockIframe(RichTextBlockDataBase):
    iframeHeight: int
    url: str

    def to_markdown(self) -> str:
        """Convert the iframe to markdown

        :return: the markdown representation of the iframe
        :rtype: str
        """
        return f"<iframe src='{self.url}' height='{self.iframeHeight}'></iframe>"

    def get_type(self) -> RichTextBlockType:
        return RichTextBlockType.IFRAME
