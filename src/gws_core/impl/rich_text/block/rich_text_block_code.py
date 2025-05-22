from gws_core.impl.rich_text.block.rich_text_block import (
    RichTextBlockDataBase, RichTextBlockType)


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

    def get_type(self) -> RichTextBlockType:
        return RichTextBlockType.CODE
