from gws_core.impl.rich_text.block.rich_text_block import (
    RichTextBlockDataBase,
    RichTextBlockTypeStandard,
)
from gws_core.impl.rich_text.block.rich_text_block_decorator import rich_text_block_decorator


@rich_text_block_decorator(RichTextBlockTypeStandard.VIDEO.value)
class RichTextBlockVideo(RichTextBlockDataBase):
    """Object representing a video block in a rich text"""

    url: str
    caption: str | None = None
    width: int = 0
    height: int = 0
    service: str = ""  # e.g., "youtube", "vimeo", etc.

    def to_markdown(self) -> str:
        """Convert the video to markdown

        :return: the markdown representation of the video
        :rtype: str
        """
        markdown = f"[Video: {self.url}]"
        if self.caption:
            markdown += f"\n*{self.caption}*"
        return markdown
