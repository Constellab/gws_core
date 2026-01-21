from enum import Enum

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.string_helper import StringHelper
from gws_core.impl.rich_text.block.rich_text_block import (
    RichTextBlockDataBase,
    RichTextBlockTypeStandard,
)
from gws_core.model.typing_manager import TypingManager


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
    type: str
    data: dict
    # tunes: Dict[str, Any]

    def is_type(self, block_type: RichTextBlockTypeStandard | str) -> bool:
        """Check if the block is of the given type

        :param block_type: the block type to check
        :type block_type: RichTextBlockType | str
        :return: True if the block is of the given type, False otherwise
        :rtype: bool
        """
        if isinstance(block_type, RichTextBlockTypeStandard):
            return self.type == block_type.value
        return self.type == block_type

    def get_data(self) -> RichTextBlockDataBase:
        # Get the block type string value
        block_typing_name = self.type

        # if the type does not contains '.', it is a built-in type
        if "." not in block_typing_name:
            block_typing_name = "RICH_TEXT_BLOCK.gws_core." + block_typing_name

        # Look up the data class from the typing manager using object_sub_type
        data_class = TypingManager.get_and_check_type_from_name(block_typing_name)

        if not issubclass(data_class, RichTextBlockDataBase):
            raise TypeError(f"Typing {block_typing_name} is not a RichTextBlockDataBase")

        if data_class is not None:
            return data_class.from_json(self.data)

        # For unknown block types, raise an error
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

    def get_block_typing_name(self) -> str:
        """Get the typing name of the block

        :return: the typing name of the block
        :rtype: str
        """
        # if the type does not contains '.', it is a built-in type
        if RichTextBlockTypeStandard.is_standard_type(self.type):
            return "RICH_TEXT_BLOCK.gws_core." + self.type
        return self.type

    def set_data(self, data: RichTextBlockDataBase) -> None:
        """Set the data of the block

        :param data: the data to set
        :type data: RichTextBlockDataBase
        """
        if self.get_block_typing_name() != data.get_typing_name():
            raise ValueError(
                f"Block type {self.get_block_typing_name()} does not match data type {data.get_typing_name()}"
            )
        self.data = data.to_json_dict()

    @staticmethod
    def from_data(data: RichTextBlockDataBase, id_: str | None = None) -> "RichTextBlock":
        """Create a RichTextBlock from data

        :param data: the data to set
        :type data: RichTextBlockDataBase
        :return: the RichTextBlock
        :rtype: RichTextBlock
        """
        block = RichTextBlock(
            id=id_ or StringHelper.generate_uuid(),
            type=data.get_str_type(),
            data=data.to_json_dict(),
        )
        return block


class RichTextDTO(BaseModelDTO):
    version: int
    editorVersion: str
    blocks: list[RichTextBlock]
