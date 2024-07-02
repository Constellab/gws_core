

from enum import Enum
from typing import Any, Dict, List, Literal, Optional, TypedDict

from gws_core.core.model.model_dto import BaseModelDTO


class RichTextBlockType(Enum):
    """List the special block type that can be used in rich text """
    FIGURE = 'figure'
    RESOURCE_VIEW = 'resourceView'
    PARAGRAPH = 'paragraph'
    HEADER = 'header'
    QUOTE = 'quote'
    HINT = 'hint'
    CODE = 'code'
    LIST = 'list'
    VIDEO = 'video'
    FORMULA = 'formula'
    TABLE = 'table'


class RichTextBlock(BaseModelDTO):
    id: str
    type: RichTextBlockType
    data: Any
    # tunes: Dict[str, Any]


class RichTextDTO(BaseModelDTO):
    version: str
    time: int
    blocks: List[RichTextBlock]


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


class RichTextParagraphHeaderData(TypedDict):
    """Object representing a paragraph block data in a rich text

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    text: str
    level: int


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
    experiment_id: str
    view_method_name: str
    view_config: Dict[str, Any]
    title: Optional[str]
    caption: Optional[str]


class RichTextENoteResourceViewData(TypedDict):
    """Object representing a resource view in an enote rich text"""
    id: str
    # key in the enote of the sub resource to call view on
    sub_resource_key: str
    view_method_name: str
    view_config: Dict[str, Any]
    title: Optional[str]
    caption: Optional[str]


################################ BLOCK DATA ################################
class RichTextVariableData(TypedDict):
    """Object representing a variable in a rich text"""
    name: str
    description: str
    value: Any
    type: Literal['string']
