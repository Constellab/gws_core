

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, TypedDict

from gws_core.core.model.model_dto import BaseModelDTO


class RichTextBlockType(Enum):
    """List the special block type that can be used in rich text """
    FIGURE = 'figure'
    RESOURCE_VIEW = 'resourceView'  # view of a resource
    FILE_VIEW = 'fileView'  # independant view stored in a file (without resource)
    NOTE_RESOURCE_VIEW = 'noteResourceView'  # view of a resource in an note
    PARAGRAPH = 'paragraph'
    HEADER = 'header'
    QUOTE = 'quote'
    HINT = 'hint'
    CODE = 'code'
    LIST = 'list'
    VIDEO = 'video'
    FORMULA = 'formula'
    TABLE = 'table'
    FILE = 'file'
    TIMESTAMP = 'timestamp'


class RichTextBlock(BaseModelDTO):
    id: str
    type: RichTextBlockType
    data: Any
    # tunes: Dict[str, Any]


class RichTextDTO(BaseModelDTO):
    version: str
    time: int
    blocks: List[RichTextBlock]


class RichTextObjectType(Enum):
    """Different object that use the rich text editor

    :param Enum: _description_
    :type Enum: _type_
    """
    NOTE = 'note'
    NOTE_TEMPLATE = 'note_template'
    NOTE_RESOURCE = 'note_resource'


################################ BLOCK DATA ################################

class RichTextParagraphData(TypedDict):
    """Object representing a paragraph block data in a rich text

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    text: str


class RichTextParagraphHeaderLevel(Enum):
    HEADER_1 = 2
    HEADER_2 = 3
    HEADER_3 = 4

    @classmethod
    def from_int(cls, level: int) -> 'RichTextParagraphHeaderLevel':
        if not isinstance(level, int):
            return cls.HEADER_1
        if level == 1:
            return cls.HEADER_1
        elif level == 2:
            return cls.HEADER_2
        else:
            return cls.HEADER_3


class RichTextParagraphHeaderData(TypedDict):
    """Object representing a paragraph block data in a rich text

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    text: str
    level: int


class RichTextParagraphListItemData(TypedDict):
    """Object representing a list block data in a rich text

    :param TypedDict: [description]
    :type TypedDict: [type]
    """

    content: str
    items: List["RichTextParagraphListItemData"]


class RichTextParagraphListData(TypedDict):
    """Object representing a list block data in a rich text

    :param TypedDict: [description]
    :type TypedDict: [type]
    """

    style: Literal['ordered', 'unordered']
    items: List[RichTextParagraphListItemData]


class RichTextFigureData(TypedDict):
    """Object representing a figure in a rich text

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    filename: str
    title: Optional[str]
    caption: Optional[str]
    width: int
    height: int
    naturalWidth: int
    naturalHeight: int


class RichTextResourceViewData(TypedDict):
    """Object representing a resource view in a rich text"""
    id: str
    view_config_id: str
    resource_id: str
    scenario_id: Optional[str]
    view_method_name: str
    view_config: Dict[str, Any]
    title: Optional[str]
    caption: Optional[str]


class RichTextNoteResourceViewData(TypedDict):
    """Object representing a resource view in an note rich text"""
    id: str
    # key in the note of the sub resource to call view on
    sub_resource_key: str
    view_method_name: str
    view_config: Dict[str, Any]
    title: Optional[str]
    caption: Optional[str]


class RichTextViewFileData(TypedDict):
    """Object representing a independant view in a rich text, the view is not associated with a resource"""
    id: str
    filename: str
    title: Optional[str]
    caption: Optional[str]


class RichTextVariableData(TypedDict):
    """Object representing a variable in a rich text"""
    name: str
    description: str
    value: Any
    type: Literal['string']


class RichTextTimestampData(TypedDict):
    """Object representing a variable in a rich text"""
    timestamp: str
    format: Literal['DATE', 'DATE_TIME', 'DATE_TIME_WITH_SECONDS', 'TIME_WITH_SECONDS', 'FROM_NOW']


class RichTextFormulaData(TypedDict):
    formula: str


class RichTextFileData(TypedDict):
    name: str
    size: int  # in bytes
