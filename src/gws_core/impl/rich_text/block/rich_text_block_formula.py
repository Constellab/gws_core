from gws_core.impl.rich_text.block.rich_text_block import (
    RichTextBlockDataBase,
    RichTextBlockTypeStandard,
)
from gws_core.impl.rich_text.block.rich_text_block_decorator import rich_text_block_decorator


@rich_text_block_decorator(RichTextBlockTypeStandard.FORMULA.value)
class RichTextBlockFormula(RichTextBlockDataBase):
    formula: str
    title: str | None = None
    caption: str | None = None

    def to_markdown(self) -> str:
        """Convert the formula to markdown

        :return: the markdown representation of the formula
        :rtype: str
        """
        return f"$$\n{self.formula}\n$$"
