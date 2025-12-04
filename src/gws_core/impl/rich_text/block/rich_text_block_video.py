from typing import Optional

from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockDataBase, RichTextBlockType


class RichTextBlockVideo(RichTextBlockDataBase):
    """Object representing a video block in a rich text"""

    url: str
    caption: Optional[str] = None
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

    def get_type(self) -> RichTextBlockType:
        return RichTextBlockType.VIDEO
