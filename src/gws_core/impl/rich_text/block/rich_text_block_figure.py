from gws_core.impl.rich_text.block.rich_text_block import (
    RichTextBlockDataBase,
    RichTextBlockTypeStandard,
)
from gws_core.impl.rich_text.block.rich_text_block_decorator import rich_text_block_decorator


@rich_text_block_decorator(RichTextBlockTypeStandard.FIGURE.value)
class RichTextBlockFigure(RichTextBlockDataBase):
    """Object representing a figure in a rich text

    :param TypedDict: [description]
    :type TypedDict: [type]
    """

    filename: str
    title: str | None = None
    caption: str | None = None
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
        return ""
