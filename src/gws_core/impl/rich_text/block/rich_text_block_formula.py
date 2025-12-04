from typing import Optional

from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockDataBase, RichTextBlockType


class RichTextBlockFormula(RichTextBlockDataBase):
    formula: str
    title: Optional[str] = None
    caption: Optional[str] = None

    def to_markdown(self) -> str:
        """Convert the formula to markdown

        :return: the markdown representation of the formula
        :rtype: str
        """
        return f"$$\n{self.formula}\n$$"

    def get_type(self) -> RichTextBlockType:
        return RichTextBlockType.FORMULA
