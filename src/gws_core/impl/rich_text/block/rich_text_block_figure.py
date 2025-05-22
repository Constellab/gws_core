from typing import Optional

from gws_core.impl.rich_text.block.rich_text_block import (
    RichTextBlockDataBase, RichTextBlockType)


class RichTextBlockFigure(RichTextBlockDataBase):
    """Object representing a figure in a rich text

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    filename: str
    title: Optional[str] = None
    caption: Optional[str] = None
    width: int
    height: int
    naturalWidth: int
    naturalHeight: int

    def to_markdown(self) -> str:
        """Convert the figure to markdown

        :return: the markdown representation of the figure
        :rtype: str
        """
        # alt_text = self.title or self.caption or self.filename
        # markdown = f"![{alt_text}]({self.filename})"

        # if self.caption:
        #     markdown += f"\n*{self.caption}*"

        # return markdown
        return ''

    def get_type(self) -> RichTextBlockType:
        return RichTextBlockType.FIGURE
