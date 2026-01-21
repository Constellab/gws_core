from gws_core.impl.rich_text.block.rich_text_block import (
    RichTextBlockDataBase,
    RichTextBlockTypeStandard,
)
from gws_core.impl.rich_text.block.rich_text_block_decorator import rich_text_block_decorator


@rich_text_block_decorator(RichTextBlockTypeStandard.CODE.value)
class RichTextBlockCode(RichTextBlockDataBase):
    """Object representing a code block in a rich text"""

    code: str
    language: str = ""

    def to_markdown(self) -> str:
        """Convert the code to markdown

        :return: the markdown representation of the code
        :rtype: str
        """
        lang = self.language if self.language else ""
        return f"```{lang}\n{self.code}\n```"
