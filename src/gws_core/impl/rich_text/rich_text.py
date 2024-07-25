

from datetime import datetime
from typing import Any, List, Optional, Set

from gws_core.core.utils.string_helper import StringHelper
from gws_core.impl.rich_text.rich_text_paragraph_text import \
    RichTextParagraphText
from gws_core.impl.rich_text.rich_text_types import (
    RichTextBlock, RichTextBlockType, RichTextDTO,
    RichTextENoteResourceViewData, RichTextFigureData, RichTextFileData,
    RichTextParagraphData, RichTextParagraphHeaderData,
    RichTextParagraphHeaderLevel, RichTextResourceViewData,
    RichTextViewFileData)
from gws_core.resource.r_field.serializable_r_field import \
    SerializableObjectJson


class RichText(SerializableObjectJson):
    """Class to manipulate the rich texts content

    :return: [description]
    :rtype: [type]
    """

    _content: RichTextDTO

    def __init__(self, rich_text_content: Optional[RichTextDTO] = None) -> None:
        if rich_text_content is None:
            self._content = self.create_rich_text_dto([])
        else:
            if not isinstance(rich_text_content, RichTextDTO):
                raise Exception('The rich text content is not valid')

            # create a copy of the DTO so the rich text manipulation doesn't affect the original DTO
            self._content = rich_text_content.model_copy(deep=True)

    ##################################### BLOCK #########################################

    def get_blocks(self) -> List[RichTextBlock]:
        return self._content.blocks

    def get_blocks_by_type(self, block_type: RichTextBlockType) -> List[RichTextBlock]:
        """Get the blocks of the given type
        """
        return [block for block in self.get_blocks() if block.type == block_type]

    def append_block(self, block: RichTextBlock) -> int:
        """
        Append a block to the rich text content

        :param block: block to add
        :type block: RichTextBlock
        :return: index of the new block
        :rtype: int
        """
        if not block.id or self.get_block_by_id(block.id) is not None:
            block.id = self.generate_id()
        self._content.blocks.append(block)

        return len(self.get_blocks()) - 1

    def _insert_block_at_index(self, index: int, block: RichTextBlock) -> None:
        """Insert an element in the rich text content at the given index
        """

        if index < 0 or index > len(self.get_blocks()):
            raise Exception('The index is not valid')

        self._content.blocks.insert(index, block)

    def _remove_block_at_index(self, block_index: int) -> RichTextBlock:
        """Remove an element from the rich text content
        """
        return self._content.blocks.pop(block_index)

    def replace_block_at_index(self, index: int, block: RichTextBlock) -> None:
        """Replace a block at the given index
        """
        if index < 0 or index > len(self.get_blocks()):
            raise Exception('The index is not valid')
        self._content.blocks[index] = block

    def get_block_at_index(self, index: int) -> RichTextBlock:
        """Get the block at the given index
        """
        if index < 0 or index > len(self.get_blocks()):
            raise Exception('The index is not valid')
        return self._content.blocks[index]

    def replace_block_by_id(self, block_id: str, block: RichTextBlock) -> None:
        """Replace a block by its id
        """
        block_index = self.get_block_index_by_id(block_id)
        if block_index >= 0:
            self.replace_block_at_index(block_index, block)

    def replace_block_data_by_id(self, block_id: str, data: Any) -> None:
        """Replace the data of a block by its id
        """
        block = self.get_block_by_id(block_id)
        if block:
            block.data = data

    def get_block_index_by_id(self, block_id: str) -> int:
        """Get the block index by its id

        :param block_id: id of the block
        :type block_id: str
        :return: index of the block (-1 if not found)
        """
        for index, current_block in enumerate(self.get_blocks()):
            if current_block.id == block_id:
                return index
        return -1

    def get_block_by_id(self, block_id: str) -> Optional[RichTextBlock]:
        """Get the block by its id

        :param block_id: id of the block
        :type block_id: str
        :return: block
        """
        for current_block in self.get_blocks():
            if current_block.id == block_id:
                return current_block
        return None

    ##################################### PARAMETER  #########################################

    def _append_or_insert_block_at_parameter(
            self, view_block: RichTextBlock, parameter_name: Optional[str] = None) -> None:
        """
        Append the block to the rich text content or insert it at the given parameter name

        :param view_block: block to add
        :type view_block: RichTextBlock
        :param parameter_name: name of the parameter where to insert the block. If None, the block is appended
        :type parameter_name: str, optional
        """

        if parameter_name is None:
            self.append_block(view_block)
        else:
            self._insert_block_at_parameter(parameter_name, view_block)

    def _insert_block_at_parameter(self, parameter_name: str, view_block: RichTextBlock) -> None:
        """Insert an element in the rich text content at the given parameter name. If the parameter name is in the middle of a text,
        the text is splitted in 3 parts (before, parameter, after)
        """

        block_index = 0
        while block_index < len(self.get_blocks()):
            current_block = self.get_blocks()[block_index]

            # only keep the paragraph blocks
            if current_block.type != RichTextBlockType.PARAGRAPH:
                block_index += 1
                continue

            paragraph_data: RichTextParagraphData = current_block.data

            if 'text' not in paragraph_data:
                block_index += 1
                continue

            paragraph_text = RichTextParagraphText(paragraph_data['text'])
            result = paragraph_text.replace_parameter_with_block(parameter_name)

            if result is not None:
                # remove current block
                self._remove_block_at_index(block_index)

                if result.before:
                    before_paragraph = self.create_paragraph(self.generate_id(), result.before)
                    self._insert_block_at_index(block_index, before_paragraph)
                    block_index += 1

                self._insert_block_at_index(block_index, view_block)
                block_index += 1

                if result.after:
                    after_paragraph = self.create_paragraph(self.generate_id(), result.after)
                    self._insert_block_at_index(block_index, after_paragraph)
                    block_index += 1

            else:
                block_index += 1

    def set_parameter(self, parameter_name: str, value: str) -> None:
        """Replace the parameter in the rich text content text
        """
        paragraphs = self.get_blocks_by_type(RichTextBlockType.PARAGRAPH)

        for paragraph in paragraphs:
            data: RichTextParagraphData = paragraph.data

            if 'text' not in data:
                continue

            paragraph_text = RichTextParagraphText(data['text'])
            new_text = paragraph_text.replace_parameter_with_text(parameter_name, value)

            if new_text is not None:
                data['text'] = new_text

    def replace_resource_views_with_parameters(self) -> None:
        """
        Method to remove the resource view from the rich text content
        and replace it when parameters. Useful when creating a template (because templates can't have resource views)
        """

        view_index = 1
        for block in self.get_blocks_by_type(RichTextBlockType.RESOURCE_VIEW):

            parameter_inline = '<te-variable-inline data-jsondata=\'{"name": "figure_' + str(view_index) + \
                '", "description": "", "type": "string", "value": ""}\'></te-variable-inline>'
            paragraph = self.create_paragraph(self.generate_id(), parameter_inline)
            self.replace_block_by_id(block.id, paragraph)
            view_index += 1

    def _format_parameter_name(self, parameter_name: str) -> str:
        return f'${parameter_name}$'

    ##################################### FIGURE #########################################
    def get_figures_data(self) -> List[RichTextFigureData]:
        return [block.data for block in self.get_blocks_by_type(RichTextBlockType.FIGURE)]

    ##################################### RESOURCE VIEW #########################################

    def get_resource_views_data(self) -> List[RichTextResourceViewData]:
        return [block.data for block in self.get_blocks_by_type(RichTextBlockType.RESOURCE_VIEW)]

    def get_file_views_data(self) -> List[RichTextViewFileData]:
        return [block.data for block in self.get_blocks_by_type(RichTextBlockType.FILE_VIEW)]

    def has_view_config(self, view_config_id: str) -> bool:
        """Check if the rich text contains a resource view with the given view_config_id
        """
        resource_views: List[RichTextResourceViewData] = self.get_resource_views_data()
        return any(rv.get('view_config_id') == view_config_id for rv in resource_views)

    def get_associated_resources(self) -> Set[str]:
        resource_views: List[RichTextResourceViewData] = self.get_resource_views_data()
        return {rv['resource_id'] for rv in resource_views}

    def add_resource_view(self, resource_view: RichTextResourceViewData,
                          parameter_name: str = None) -> RichTextBlock:

        block: RichTextBlock = self.create_block(self.generate_id(), RichTextBlockType.RESOURCE_VIEW, resource_view)
        self._append_or_insert_block_at_parameter(block, parameter_name)
        return block

    def add_enote_resource_view(self, resource_view: RichTextENoteResourceViewData,
                                parameter_name: str = None) -> RichTextBlock:
        """
        Add a view to a rich text content used in enote. This requires the enote to call the view

        :param resource_view: view to add
        :type resource_view: RichTextENoteResourceViewData
        :param parameter_name: name of the parameter where to insert the block. If None, the block is appended
        :type parameter_name: str, optional
        """
        block: RichTextBlock = self.create_block(self.generate_id(), RichTextBlockType.ENOTE_VIEW, resource_view)
        self._append_or_insert_block_at_parameter(block, parameter_name)
        return block

    def add_file_view(self, file_view: RichTextViewFileData,
                      parameter_name: str = None) -> RichTextBlock:
        """
        Add a view to a rich text content. This view is not associated with a resource

        :param file_view: view to add
        :type file_view: RichTextViewFileData
        :param parameter_name: name of the parameter where to insert the block. If None, the block is appended
        :type parameter_name: str, optional
        """
        block: RichTextBlock = self.create_block(self.generate_id(), RichTextBlockType.FILE_VIEW, file_view)
        self._append_or_insert_block_at_parameter(block, parameter_name)
        return block

    ##################################### PARAGRAPH #########################################

    def add_paragraph(self, text: str) -> RichTextBlock:
        """Add a paragraph to the rich text content
        """
        block = self.create_paragraph(self.generate_id(), text)
        self.append_block(block)
        return block

    ##################################### HEADER #########################################

    def add_header(self, text: str, level: RichTextParagraphHeaderLevel) -> RichTextBlock:
        """Add a header to the rich text content
        """
        block = self.create_header(self.generate_id(), text, level)
        self.append_block(block)
        return block

    ##################################### FIGURE #########################################

    def add_figure(self, figure_data: RichTextFigureData,
                   parameter_name: str = None) -> RichTextBlock:
        """Add a figure to the rich text content
        """
        block: RichTextBlock = self.create_block(self.generate_id(), RichTextBlockType.FIGURE, figure_data)
        self._append_or_insert_block_at_parameter(block, parameter_name)
        return block

    ##################################### FILE #########################################

    def get_files_data(self) -> List[RichTextFileData]:
        return [block.data for block in self.get_blocks_by_type(RichTextBlockType.FILE)]

    def add_file(self, file_data: RichTextFileData,
                 parameter_name: str = None) -> RichTextBlock:
        """Add a file to the rich text content
        """
        block: RichTextBlock = self.create_block(self.generate_id(), RichTextBlockType.FILE, file_data)
        self._append_or_insert_block_at_parameter(block, parameter_name)
        return block

    ##################################### OTHERS #########################################

    def get_content(self) -> RichTextDTO:
        return self._content

    def get_content_as_json(self) -> dict:
        return self._content.to_json_dict()

    def is_empty(self) -> bool:
        if self._content is None or not self._content.blocks or len(self._content.blocks) == 0:
            return True

        for block in self._content.blocks:
            if block.type != RichTextBlockType.PARAGRAPH:
                return False
            if 'text' in block.data and block.data['text']:
                return False

        return True

    def generate_id(self) -> str:
        while True:
            id_ = StringHelper.generate_random_chars(10)
            if not self.get_block_by_id(id_):
                return id_

    def append_rich_text(self, rich_text: 'RichText') -> None:
        for block in rich_text.get_blocks():
            self.append_block(block)

    ##################################### SERIALIZATION / DESERIALIZATION #########################################

    def serialize(self) -> dict:
        """ Serialize the object into a json object.
        For SerializableRField, this method is called when the resource is saved.

        :return: _description_
        :rtype: Union[Dict, List, str, bool, float]
        """
        return self._content.to_json_dict()

    @classmethod
    def deserialize(cls, data: dict) -> 'RichText':
        """ Deserialize the object from a json object.
        For SerializableRField, this method is called when the RField is loaded.

        :param data: json object generated by the serialize method
        :type data: Union[Dict, List, str, bool, float]
        :return: _description_
        :rtype: SerializableObjectJson
        """
        if data is None:
            return RichText()
        return RichText(RichTextDTO.from_json(data))
    ##################################### CLASS METHODS #########################################

    @classmethod
    def create_paragraph(cls, id_: str, text: str) -> RichTextBlock:
        """Create a paragraph block
        """
        data: RichTextParagraphData = {'text': text}
        return cls.create_block(id_, RichTextBlockType.PARAGRAPH, data)

    @classmethod
    def create_header(cls, id_: str, text: str, level: RichTextParagraphHeaderLevel) -> RichTextBlock:
        """Create a paragraph block
        """
        if not text:
            raise ValueError('The text is empty')
        if not isinstance(level, RichTextParagraphHeaderLevel):
            raise ValueError('The level is not valid')

        header_data: RichTextParagraphHeaderData = {'text': text, 'level': level.value}
        return cls.create_block(id_, RichTextBlockType.HEADER, header_data)

    @classmethod
    def create_block(cls, id_: str, block_type: RichTextBlockType, data: Any) -> RichTextBlock:
        """Create a block
        """
        return RichTextBlock(
            id=id_,
            type=block_type,
            data=data,
        )

    @classmethod
    def create_rich_text_dto(cls, blocks: List[RichTextBlock]) -> RichTextDTO:
        return RichTextDTO(
            blocks=blocks,
            version="2.9.0",
            time=int(datetime.now().timestamp() * 1000)
        )
