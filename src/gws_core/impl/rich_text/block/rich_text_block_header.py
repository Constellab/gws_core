from enum import Enum

from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockDataBase, RichTextBlockType


class RichTextBlockHeaderLevel(Enum):
    HEADER_1 = 2
    HEADER_2 = 3
    HEADER_3 = 4

    @classmethod
    def from_int(cls, level: int) -> "RichTextBlockHeaderLevel":
        if not isinstance(level, int):
            return cls.HEADER_1
        if level == 1:
            return cls.HEADER_1
        elif level == 2:
            return cls.HEADER_2
        else:
            return cls.HEADER_3

    def to_markdown(self) -> str:
        """Convert the header level to markdown

        :return: the markdown representation of the header level
        :rtype: str
        """
        if self == RichTextBlockHeaderLevel.HEADER_1:
            return "##"
        elif self == RichTextBlockHeaderLevel.HEADER_2:
            return "###"
        else:
            return "####"


class RichTextBlockHeader(RichTextBlockDataBase):
    """Object representing a paragraph block data in a rich text

    :param TypedDict: [description]
    :type TypedDict: [type]
    """

    text: str
    level: RichTextBlockHeaderLevel

    def to_markdown(self) -> str:
        """Convert the header to markdown

        :return: the markdown representation of the header
        :rtype: str
        """
        return f"{self.level.to_markdown()} {self.text}"

    def get_type(self) -> RichTextBlockType:
        return RichTextBlockType.HEADER
