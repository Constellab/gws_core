from gws_core.impl.file.file_helper import FileHelper
from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockDataBase, RichTextBlockType


class RichTextBlockFile(RichTextBlockDataBase):
    name: str
    size: int  # in bytes

    def to_markdown(self) -> str:
        """Convert the file to markdown

        :return: the markdown representation of the file
        :rtype: str
        """

        return f"[File: {self.name} ({FileHelper.get_file_size_pretty_text(self.size)})]"

    def get_type(self) -> RichTextBlockType:
        return RichTextBlockType.FILE
