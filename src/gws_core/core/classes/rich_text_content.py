# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from typing_extensions import NotRequired, TypedDict

from gws_core.core.utils.string_helper import StringHelper


class RichTextOps(TypedDict):
    insert: Any
    attributes: NotRequired[Dict[str, Any]]


class RichTextBlock(TypedDict):
    id: str
    type: str
    data: Dict[str, Any]
    # tunes: Dict[str, Any]


class RichTextI(TypedDict):

    version: Optional[str]

    time: Optional[int]

    blocks: List[RichTextBlock]


class RichTextBlockType(Enum):
    """List the special block type that can be used in rich text """
    FIGURE = 'figure'
    RESOURCE_VIEW = 'resourceView'
    PARAGRAPH = 'paragraph'


class RichTextParagraphData(TypedDict):
    """Object representing a paragraph block data in a rich text

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    text: str


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
    # technical_info: List[Dict]


class RichText():
    """Class to manipulate the rich texts content

    :return: [description]
    :rtype: [type]
    """

    _content: RichTextI

    def __init__(self, rich_text_content: RichTextI) -> None:
        if not isinstance(rich_text_content, dict) or 'blocks' not in rich_text_content:
            raise Exception('The content is not correclty formatted')
        self._content = rich_text_content

    def is_empty(self) -> bool:
        return self._content is None or not self._content['blocks'] or len(self._content['blocks']) == 0

    def get_blocks(self) -> List[RichTextBlock]:
        return self._content['blocks']

    def get_figures_data(self) -> List[RichTextFigureData]:
        return [block['data'] for block in self.get_block(RichTextBlockType.FIGURE)]

    def get_resource_views_data(self) -> List[RichTextResourceViewData]:
        return [block['data'] for block in self.get_block(RichTextBlockType.RESOURCE_VIEW)]

    def has_view_config(self, view_config_id: str) -> bool:
        """Check if the rich text contains a resource view with the given view_config_id
        """
        resource_views: List[RichTextResourceViewData] = self.get_resource_views_data()
        return any(rv.get('view_config_id') == view_config_id for rv in resource_views)

    def get_associated_resources(self) -> Set[str]:
        resource_views: List[RichTextResourceViewData] = self.get_resource_views_data()
        return {rv['resource_id'] for rv in resource_views}

    def get_block(self, block_type: RichTextBlockType) -> List[RichTextBlock]:
        """Get the blocks of the given type
        """
        return [block for block in self.get_blocks() if block['type'] == block_type.value]

    def add_resource_views(self, resource_view: RichTextResourceViewData, variable_name: str = None) -> None:

        block: RichTextBlock = self.create_block(RichTextBlockType.RESOURCE_VIEW, resource_view)
        if variable_name is None:
            self._append_block(block)
        else:
            self._insert_block_at_variable(variable_name, block)

    def _append_block(self, block: RichTextBlock) -> None:
        """Append an element to the rich text content
        """
        self._content['blocks'].append(block)

    def _insert_block_at_index(self, index: int, block: RichTextBlock) -> None:
        """Insert an element in the rich text content at the given index
        """

        if index < 0 or index > len(self.get_blocks()):
            raise Exception('The index is not valid')

        self._content['blocks'].insert(index, block)

    def _insert_block_at_variable(self, variable_name: str, view_block: RichTextBlock) -> None:
        """Insert an element in the rich text content at the given variable name. If the variable name is in the middle of a text,
        the text is splitted in 3 parts (before, variable, after)
        """

        block_index = 0
        variable_name = self._format_variable_name(variable_name)
        while block_index < len(self.get_blocks()):
            current_block = self.get_blocks()[block_index]

            # only keep the paragraph blocks
            if current_block['type'] != RichTextBlockType.PARAGRAPH.value:
                block_index += 1
                continue

            paragraph_data: RichTextParagraphData = current_block['data']

            if 'text' not in paragraph_data:
                block_index += 1
                continue

            # if the block contains the variable name, split the string
            if variable_name in paragraph_data['text']:
                # remove current block
                self._remove_block_at_index(block_index)

                # split the string
                splitted = paragraph_data['text'].split(variable_name)

                # replace the current block by 3 blocks (before, variable, after)
                if splitted[0]:
                    before_paragraph = self.create_paragraph(splitted[0])
                    # add a \n at the end to finish the previous block
                    self._insert_block_at_index(block_index, before_paragraph)
                    block_index += 1

                # add the view block
                self._insert_block_at_index(block_index, view_block)
                block_index += 1

                if splitted[1]:
                    after_paragraph = self.create_paragraph(splitted[1])
                    self._insert_block_at_index(block_index, after_paragraph)
                    block_index += 1

            else:
                block_index += 1

    def _remove_block_at_index(self, block_index: int) -> RichTextBlock:
        """Remove an element from the rich text content
        """
        return self._content['blocks'].pop(block_index)

    def get_content(self) -> RichTextI:
        return self._content

    def replace_variable(self, variable_name: str, value: str) -> None:
        """Replace the variable in the rich text content text
        """
        variable_name = self._format_variable_name(variable_name)

        paragraphs = self.get_block(RichTextBlockType.PARAGRAPH)

        for paragraph in paragraphs:
            data: RichTextParagraphData = paragraph['data']

            if 'text' not in data:
                continue

            if variable_name in data['text']:
                data['text'] = data['text'].replace(variable_name, value)

    def add_paragraph(self, paragraph: str) -> None:
        """Add a paragraph to the rich text content
        """
        self._append_block(paragraph)

    def replace_resource_views_with_variables(self):
        """Method to remove the resource view from the rich text content
         and replace it when variables. Useful when creating a template (because templates can't have resource views)
        """

        block_index = 0
        view_index = 1
        for block in self.get_block():

            if block['type'] == RichTextBlockType.RESOURCE_VIEW.value:
                variable = self._format_variable_name(f"figure_{view_index}")
                paragraph = self.create_paragraph(variable)
                self.replace_block_at_index(block_index, paragraph)
                view_index += 1
            block_index += 1

    def replace_block_at_index(self, index: int, block: RichTextBlock) -> None:
        """Replace a block at the given index
        """
        if index < 0 or index > len(self.get_blocks()):
            raise Exception('The index is not valid')
        self._content['blocks'][index] = block

    def _format_variable_name(self, variable_name: str) -> str:
        return f'${variable_name}$'

    ##################################### CLASS METHODS #########################################

    @classmethod
    def create_paragraph(cls, text: str) -> RichTextBlock:
        """Create a paragraph block
        """
        return cls.create_block(RichTextBlockType.PARAGRAPH, {'text': text})

    @classmethod
    def create_block(cls, block_type: RichTextBlockType, data: Dict[str, Any]) -> RichTextBlock:
        """Create a block
        """
        return {
            "id": StringHelper.generate_random_chars(10),
            'type': block_type.value,
            'data': data,
        }

    @classmethod
    def create_rich_text_i(cls, blocks: List[RichTextBlock]) -> RichTextI:
        return {
            "blocks": blocks,
            "version": "2.28.2",
            'time': int(datetime.now().timestamp() * 1000)
        }
