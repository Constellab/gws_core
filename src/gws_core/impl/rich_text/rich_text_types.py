from enum import Enum

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.string_helper import StringHelper
from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockDataBase, RichTextBlockType
from gws_core.impl.rich_text.block.rich_text_block_code import RichTextBlockCode
from gws_core.impl.rich_text.block.rich_text_block_figure import RichTextBlockFigure
from gws_core.impl.rich_text.block.rich_text_block_file import RichTextBlockFile
from gws_core.impl.rich_text.block.rich_text_block_formula import RichTextBlockFormula
from gws_core.impl.rich_text.block.rich_text_block_header import RichTextBlockHeader
from gws_core.impl.rich_text.block.rich_text_block_hint import RichTextBlockHint
from gws_core.impl.rich_text.block.rich_text_block_iframe import RichTextBlockIframe
from gws_core.impl.rich_text.block.rich_text_block_list import RichTextBlockList
from gws_core.impl.rich_text.block.rich_text_block_paragraph import RichTextBlockParagraph
from gws_core.impl.rich_text.block.rich_text_block_quote import RichTextBlockQuote
from gws_core.impl.rich_text.block.rich_text_block_table import RichTextBlockTable
from gws_core.impl.rich_text.block.rich_text_block_timestamp import RichTextBlockTimestamp
from gws_core.impl.rich_text.block.rich_text_block_video import RichTextBlockVideo
from gws_core.impl.rich_text.block.rich_text_block_view import (
    RichTextBlockNoteResourceView,
    RichTextBlockResourceView,
    RichTextBlockViewFile,
)


class RichTextObjectType(Enum):
    """Different object that use the rich text editor

    :param Enum: _description_
    :type Enum: _type_
    """

    NOTE = "note"
    NOTE_TEMPLATE = "note_template"
    NOTE_RESOURCE = "note_resource"


####################################### RICH TEXT #######################################


class RichTextBlock(BaseModelDTO):
    id: str
    type: RichTextBlockType
    data: dict
    # tunes: Dict[str, Any]

    def get_data(self) -> RichTextBlockDataBase:
        if self.type == RichTextBlockType.PARAGRAPH:
            return RichTextBlockParagraph.from_json(self.data)
        elif self.type == RichTextBlockType.HEADER:
            return RichTextBlockHeader.from_json(self.data)
        elif self.type == RichTextBlockType.LIST:
            return RichTextBlockList.from_json(self.data)
        elif self.type == RichTextBlockType.FIGURE:
            return RichTextBlockFigure.from_json(self.data)
        elif self.type == RichTextBlockType.RESOURCE_VIEW:
            return RichTextBlockResourceView.from_json(self.data)
        elif self.type == RichTextBlockType.NOTE_RESOURCE_VIEW:
            return RichTextBlockNoteResourceView.from_json(self.data)
        elif self.type == RichTextBlockType.FILE_VIEW:
            return RichTextBlockViewFile.from_json(self.data)
        elif self.type == RichTextBlockType.TIMESTAMP:
            return RichTextBlockTimestamp.from_json(self.data)
        elif self.type == RichTextBlockType.FORMULA:
            return RichTextBlockFormula.from_json(self.data)
        elif self.type == RichTextBlockType.QUOTE:
            return RichTextBlockQuote.from_json(self.data)
        elif self.type == RichTextBlockType.HINT:
            return RichTextBlockHint.from_json(self.data)
        elif self.type == RichTextBlockType.CODE:
            return RichTextBlockCode.from_json(self.data)
        elif self.type == RichTextBlockType.VIDEO:
            return RichTextBlockVideo.from_json(self.data)
        elif self.type == RichTextBlockType.TABLE:
            return RichTextBlockTable.from_json(self.data)
        elif self.type == RichTextBlockType.FILE:
            return RichTextBlockFile.from_json(self.data)
        elif self.type == RichTextBlockType.IFRAME:
            return RichTextBlockIframe.from_json(self.data)
        raise ValueError(f"Unknown block type: {self.type}")

    def to_markdown(self) -> str:
        """Convert the block to markdown

        :return: the markdown representation of the block
        :rtype: str
        """
        try:
            data = self.get_data()
            if isinstance(data, RichTextBlockDataBase):
                return data.to_markdown()
        except Exception:
            # If any error occurs during conversion, return empty string
            pass
        return ""

    def set_data(self, data: RichTextBlockDataBase) -> None:
        """Set the data of the block

        :param data: the data to set
        :type data: RichTextBlockDataBase
        """
        if self.type != data.get_type():
            raise ValueError(f"Block type {self.type} does not match data type {data.get_type()}")
        self.data = data.to_json_dict()

    @staticmethod
    def from_data(data: RichTextBlockDataBase, id_: str = None) -> "RichTextBlock":
        """Create a RichTextBlock from data

        :param data: the data to set
        :type data: RichTextBlockDataBase
        :return: the RichTextBlock
        :rtype: RichTextBlock
        """
        block = RichTextBlock(
            id=id_ or StringHelper.generate_uuid(), type=data.get_type(), data=data.to_json_dict()
        )
        return block


class RichTextDTO(BaseModelDTO):
    version: int
    editorVersion: str
    blocks: list[RichTextBlock]
