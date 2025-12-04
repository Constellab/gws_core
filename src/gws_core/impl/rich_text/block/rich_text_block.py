from abc import abstractmethod
from enum import Enum

from gws_core.core.model.model_dto import BaseModelDTO


class RichTextBlockType(Enum):
    """List the special block type that can be used in rich text"""

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


class RichTextBlockDataBase(BaseModelDTO):
    @abstractmethod
    def to_markdown(self) -> str:
        """Convert the block to markdown

        :return: the markdown representation of the block
        :rtype: str
        """

    @abstractmethod
    def get_type(self) -> RichTextBlockType:
        """Get the type of the block

        :return: the type of the block
        :rtype: RichTextBlockType
        """
