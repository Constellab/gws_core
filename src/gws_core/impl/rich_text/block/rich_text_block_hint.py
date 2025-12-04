from typing import Literal

from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockDataBase, RichTextBlockType


class RichTextBlockHint(RichTextBlockDataBase):
    """Object representing a hint block in a rich text"""

    content: str
    hintType: Literal["info", "warning", "science"] = "info"

    def to_markdown(self) -> str:
        """Convert the hint to markdown

        :return: the markdown representation of the hint
        :rtype: str
        """
        icon = {"info": "ℹ️", "warning": "⚠️", "science": "🔬"}.get(self.hintType, "ℹ️")

        return f"{icon} **{self.hintType.upper()}**: {self.content}"

    def get_type(self) -> RichTextBlockType:
        return RichTextBlockType.HINT
