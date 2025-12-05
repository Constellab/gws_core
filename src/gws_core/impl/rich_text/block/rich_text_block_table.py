
from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockDataBase, RichTextBlockType


class RichTextBlockTable(RichTextBlockDataBase):
    """Object representing a table block in a rich text"""

    content: list[list[str]]
    withHeadings: bool = False
    stretched: bool = False

    def to_markdown(self) -> str:
        """Convert the table to markdown

        :return: the markdown representation of the table
        :rtype: str
        """
        if not self.content or len(self.content) == 0:
            return ""

        result = []

        # Add table rows
        for i, row in enumerate(self.content):
            result.append("| " + " | ".join(row) + " |")

            # Add header separator
            if i == 0 and self.withHeadings:
                result.append("| " + " | ".join(["---"] * len(row)) + " |")

        return "\n".join(result)

    def get_type(self) -> RichTextBlockType:
        return RichTextBlockType.TABLE
