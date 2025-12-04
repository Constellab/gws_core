from typing import Literal

from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockDataBase, RichTextBlockType


class RichTextBlockTimestamp(RichTextBlockDataBase):
    """Object representing a variable in a rich text"""

    timestamp: str
    format: Literal[
        "DATE", "DATE_TIME", "DATE_TIME_WITH_SECONDS", "TIME_WITH_SECONDS", "FROM_NOW"
    ] = "DATE_TIME"

    def to_markdown(self) -> str:
        """Convert the timestamp to markdown

        :return: the markdown representation of the timestamp
        :rtype: str
        """
        return f"[Timestamp: {self.timestamp} ({self.format})]"

    def get_type(self) -> RichTextBlockType:
        return RichTextBlockType.TIMESTAMP
