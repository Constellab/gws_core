from abc import abstractmethod
from enum import Enum

from gws_core.core.model.base_typing import BaseTyping
from gws_core.core.model.model_dto import BaseModelDTO


class RichTextBlockTypeStandard(Enum):
    """List the standard block type that can be used in rich text"""

    PARAGRAPH = "paragraph"
    HEADER = "header"
    LIST = "list"
    FIGURE = "figure"
    RESOURCE_VIEW = "resourceView"  # view of a resource
    NOTE_RESOURCE_VIEW = "noteResourceView"  # view of a resource in an note
    FILE_VIEW = "fileView"  # independant view stored in a file (without resource)
    TIMESTAMP = "timestamp"
    FORMULA = "formula"
    QUOTE = "quote"
    HINT = "hint"
    CODE = "code"
    VIDEO = "video"
    TABLE = "table"
    FILE = "file"
    IFRAME = "iframe"
    HTML = "html"

    @staticmethod
    def is_standard_type(block_type: str) -> bool:
        """Check if the given block type is a standard type

        :param block_type: the block type to check
        :type block_type: str
        :return: True if the block type is a standard type, False otherwise
        :rtype: bool
        """
        return block_type in [item.value for item in RichTextBlockTypeStandard]


class RichTextBlockDataBase(BaseModelDTO, BaseTyping):
    @abstractmethod
    def to_markdown(self) -> str:
        """Convert the block to markdown

        :return: the markdown representation of the block
        :rtype: str
        """

    def get_str_type(self) -> str:
        """Get the type of the block

        :return: the type of the block
        :rtype: str
        """

        type_ = self.get_typing_name_obj().unique_name
        if RichTextBlockTypeStandard.is_standard_type(type_):
            return type_
        return self.get_typing_name()


class RichTextBlockDataSpecial(RichTextBlockDataBase):
    @abstractmethod
    def to_html(self) -> str:
        """Convert the block to html.
        This is usefule to render special block within the normal note context where
        special block are not natively supported.
        In this case the special block are converted to basic html that can be rendered in the note.

        :return: the html representation of the block
        :rtype: str
        """
