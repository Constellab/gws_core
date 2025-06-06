import re
from typing import List, Optional, Set, cast

from gws_core.core.utils.string_helper import StringHelper
from gws_core.impl.rich_text.block.rich_text_block import (
    RichTextBlockDataBase, RichTextBlockType)
from gws_core.impl.rich_text.block.rich_text_block_figure import \
    RichTextBlockFigure
from gws_core.impl.rich_text.block.rich_text_block_file import \
    RichTextBlockFile
from gws_core.impl.rich_text.block.rich_text_block_formula import \
    RichTextBlockFormula
from gws_core.impl.rich_text.block.rich_text_block_header import (
    RichTextBlockHeader, RichTextBlockHeaderLevel)
from gws_core.impl.rich_text.block.rich_text_block_list import \
    RichTextBlockList
from gws_core.impl.rich_text.block.rich_text_block_paragraph import \
    RichTextBlockParagraph
from gws_core.impl.rich_text.block.rich_text_block_timestamp import \
    RichTextBlockTimestamp
from gws_core.impl.rich_text.block.rich_text_block_view import (
    RichTextBlockNoteResourceView, RichTextBlockResourceView,
    RichTextBlockViewFile)
from gws_core.impl.rich_text.rich_text_migrator import TeRichTextMigrator
from gws_core.impl.rich_text.rich_text_types import RichTextBlock, RichTextDTO
from gws_core.resource.r_field.serializable_r_field import \
    SerializableObjectJson


class RichText(SerializableObjectJson):
    """Class to manipulate the rich texts content

    :return: [description]
    :rtype: [type]
    """
    CURRENT_VERION = 2
    CURRENT_EDITOR_VERSION = '2.30.2'

    version: int
    editor_version: str

    blocks: List[RichTextBlock]

    def __init__(self, rich_text_dto: Optional[RichTextDTO] = None,
                 target_version: int = None) -> None:

        if target_version is None:
            target_version = RichText.CURRENT_VERION

        if rich_text_dto is None:
            rich_text_dto = self.create_rich_text_dto([])
        else:
            if not isinstance(rich_text_dto, RichTextDTO):
                raise Exception('The rich text content is not valid')

            # create a copy of the DTO so the rich text manipulation doesn't affect the original DTO
            rich_text_dto = rich_text_dto.model_copy(deep=True)

        migrated_rich_text = TeRichTextMigrator.migrate(rich_text_dto, target_version)
        self.version = migrated_rich_text.version
        self.editor_version = migrated_rich_text.editorVersion
        self.blocks = migrated_rich_text.blocks

    ##################################### BLOCK #########################################

    def get_blocks(self) -> List[RichTextBlock]:
        return self.blocks

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
        self.blocks.append(block)

        return len(self.get_blocks()) - 1

    def insert_block_at_index(self, index: int, block: RichTextBlock) -> None:
        """Insert an element in the rich text content at the given index
        """

        if index < 0 or index > len(self.get_blocks()):
            raise Exception('The index is not valid')

        self.blocks.insert(index, block)

    def _remove_block_at_index(self, block_index: int) -> RichTextBlock:
        """Remove an element from the rich text content
        """
        return self.blocks.pop(block_index)

    def replace_block_at_index(self, index: int, block: RichTextBlock) -> None:
        """Replace a block at the given index
        """
        if index < 0 or index > len(self.get_blocks()):
            raise Exception('The index is not valid')
        self.blocks[index] = block

    def get_block_at_index(self, index: int) -> RichTextBlock:
        """Get the block at the given index
        """
        if index < 0 or index > len(self.get_blocks()):
            raise Exception('The index is not valid')
        return self.blocks[index]

    def replace_block_by_id(self, block_id: str, block: RichTextBlock) -> None:
        """Replace a block by its id
        """
        block_index = self.get_block_index_by_id(block_id)
        if block_index >= 0:
            self.replace_block_at_index(block_index, block)

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

            paragraph_data = current_block.get_data()

            if not isinstance(paragraph_data, RichTextBlockParagraph):
                block_index += 1
                continue

            result = paragraph_data.replace_parameter_with_block(parameter_name)

            if result is not None:
                # remove current block
                self._remove_block_at_index(block_index)

                if result.before:
                    before_paragraph = self.create_paragraph(self.generate_id(), result.before)
                    self.insert_block_at_index(block_index, before_paragraph)
                    block_index += 1

                self.insert_block_at_index(block_index, view_block)
                block_index += 1

                if result.after:
                    after_paragraph = self.create_paragraph(self.generate_id(), result.after)
                    self.insert_block_at_index(block_index, after_paragraph)
                    block_index += 1

            else:
                block_index += 1

    def set_parameter(self, parameter_name: str, value: str,
                      replace_block: bool = False) -> None:
        """Replace the parameter in the rich text content text
        """
        paragraphs = self.get_blocks_by_type(RichTextBlockType.PARAGRAPH)

        for paragraph in paragraphs:
            data = paragraph.get_data()

            if not isinstance(data, RichTextBlockParagraph):
                continue

            data.replace_parameter_with_text(parameter_name, value, replace_block)
            paragraph.set_data(data)

    def delete_parameter(self, parameter_name: str) -> None:
        """Delete the parameter in the rich text content text
        """
        self.set_parameter(parameter_name, '', True)

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
    def get_figures_data(self) -> List[RichTextBlockFigure]:
        return [cast(RichTextBlockFigure, block.get_data()) for block in self.get_blocks_by_type(RichTextBlockType.FIGURE)]

    ##################################### RESOURCE VIEW #########################################

    def get_resource_views_data(self) -> List[RichTextBlockResourceView]:
        return [cast(RichTextBlockResourceView, block.get_data()) for block in self.get_blocks_by_type(RichTextBlockType.RESOURCE_VIEW)]

    def get_file_views_data(self) -> List[RichTextBlockViewFile]:
        return [cast(RichTextBlockViewFile, block.get_data()) for block in self.get_blocks_by_type(RichTextBlockType.FILE_VIEW)]

    def has_view_config(self, view_config_id: str) -> bool:
        """Check if the rich text contains a resource view with the given view_config_id
        """
        resource_views: List[RichTextBlockResourceView] = self.get_resource_views_data()
        return any(rv.view_config_id == view_config_id for rv in resource_views)

    def get_associated_resources(self) -> Set[str]:
        resource_views: List[RichTextBlockResourceView] = self.get_resource_views_data()
        return {rv.resource_id for rv in resource_views}

    def add_resource_view(self, resource_view: RichTextBlockResourceView,
                          parameter_name: str = None) -> RichTextBlock:

        block: RichTextBlock = self.create_block(self.generate_id(), RichTextBlockType.RESOURCE_VIEW, resource_view)
        self._append_or_insert_block_at_parameter(block, parameter_name)
        return block

    def add_note_resource_view(self, resource_view: RichTextBlockNoteResourceView,
                               parameter_name: str = None) -> RichTextBlock:
        """
        Add a view to a rich text content used in note. This requires the note to call the view

        :param resource_view: view to add
        :type resource_view: RichTextNoteResourceViewData
        :param parameter_name: name of the parameter where to insert the block. If None, the block is appended
        :type parameter_name: str, optional
        """
        block: RichTextBlock = self.create_block(
            self.generate_id(),
            RichTextBlockType.NOTE_RESOURCE_VIEW, resource_view)
        self._append_or_insert_block_at_parameter(block, parameter_name)
        return block

    def add_file_view(self, file_view: RichTextBlockViewFile,
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

    def add_header(self, text: str, level: RichTextBlockHeaderLevel) -> RichTextBlock:
        """Add a header to the rich text content
        """
        block = self.create_header(self.generate_id(), text, level)
        self.append_block(block)
        return block

    ##################################### LIST #########################################

    def add_list(self, data: RichTextBlockList) -> RichTextBlock:
        """Add a list to the rich text content
        """
        block = self.create_list(self.generate_id(), data)
        self.append_block(block)
        return block

    ##################################### FIGURE #########################################

    def add_figure(self, figure_data: RichTextBlockFigure,
                   parameter_name: str = None) -> RichTextBlock:
        """Add a figure to the rich text content
        """
        block: RichTextBlock = self.create_block(self.generate_id(), RichTextBlockType.FIGURE, figure_data)
        self._append_or_insert_block_at_parameter(block, parameter_name)
        return block

    ##################################### FILE #########################################

    def get_files_data(self) -> List[RichTextBlockFile]:
        return [cast(RichTextBlockFile, block.get_data()) for block in self.get_blocks_by_type(RichTextBlockType.FILE)]

    def add_file(self, file_data: RichTextBlockFile,
                 parameter_name: str = None) -> RichTextBlock:
        """Add a file to the rich text content
        """
        block: RichTextBlock = self.create_block(self.generate_id(), RichTextBlockType.FILE, file_data)
        self._append_or_insert_block_at_parameter(block, parameter_name)
        return block

    ##################################### FORMULA #########################################

    def add_formula(self, formula: str,
                    parameter_name: str = None) -> RichTextBlock:
        """Add a math formula to the rich text content

        :param formula_data: math formula using the KaTeX syntax
        :type formula_data: str
        :param parameter_name: name of the parameter where to insert the block. If None, the block is appended
        :type parameter_name: str, optional
        :return: _description_
        :rtype: RichTextBlock
        """
        block: RichTextBlock = self.create_formula(self.generate_id(), formula)
        self._append_or_insert_block_at_parameter(block, parameter_name)
        return block

    ##################################### TIME STAMP #########################################

    def add_timestamp(self, timestamp_data: RichTextBlockTimestamp,
                      parameter_name: str = None) -> RichTextBlock:
        """Add a timestamp to the rich text content
        """
        block: RichTextBlock = self.create_timestamp(self.generate_id(), timestamp_data)
        self._append_or_insert_block_at_parameter(block, parameter_name)
        return block

    ##################################### OTHERS #########################################

    def to_dto(self) -> RichTextDTO:
        return RichTextDTO(
            version=self.version,
            editorVersion=self.editor_version,
            blocks=self.blocks
        )

    def to_dto_json_dict(self) -> dict:
        return self.to_dto().to_json_dict()

    def to_json_file(self, file_path: str) -> None:
        str_dict = self.to_dto().to_json_str()
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(str_dict)

    def to_markdown(self) -> str:
        """Convert the rich text content to markdown
        """
        markdowns = [block.get_data().to_markdown() for block in self.get_blocks()]
        markdown = '\n\n'.join(markdown for markdown in markdowns if markdown) + '\n'

        # Process inline styles
        markdown = self._process_markdown_inline_styles(markdown)

        return markdown

    def _process_markdown_inline_styles(self, text: str) -> str:
        """Convert inline HTML tags to their markdown equivalents

        :param text: Text with HTML tags
        :type text: str
        :return: Text with markdown syntax
        :rtype: str
        """

        # Bold: <b>text</b> -> **text**
        text = re.sub(r'<b>(.*?)</b>', r'**\1**', text)

        # Italic: <i>text</i> -> *text*
        text = re.sub(r'<i>(.*?)</i>', r'*\1*', text)

        # Underline: <u>text</u> -> __text__
        text = re.sub(r'<u>(.*?)</u>', r'__\1__', text)

        # Strikethrough: <s>text</s> or <strike>text</strike> -> ~~text~~
        text = re.sub(r'<s>(.*?)</s>', r'~~\1~~', text)
        text = re.sub(r'<strike>(.*?)</strike>', r'~~\1~~', text)

        # Code: <code>text</code> -> `text`
        text = re.sub(r'<code>(.*?)</code>', r'`\1`', text)

        # Link: <a href="url">text</a> -> [text](url)
        text = re.sub(r'<a href="(.*?)">(.*?)</a>', r'[\2](\1)', text)

        return text

    def is_empty(self) -> bool:
        if not self.blocks or len(self.blocks) == 0:
            return True

        for block in self.blocks:
            data = block.get_data()
            if not isinstance(data, RichTextBlockParagraph):
                return False

            if not data.is_empty():
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
        return self.to_dto_json_dict()

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
        return cls.create_block(id_, RichTextBlockType.PARAGRAPH, RichTextBlockParagraph(text=text))

    @classmethod
    def create_header(cls, id_: str, text: str, level: RichTextBlockHeaderLevel) -> RichTextBlock:
        """Create a paragraph block
        """
        if not text:
            raise ValueError('The text is empty')
        if not isinstance(level, RichTextBlockHeaderLevel):
            raise ValueError('The level is not valid')

        header_data = RichTextBlockHeader(text=text, level=level)
        return cls.create_block(id_, RichTextBlockType.HEADER, header_data)

    @classmethod
    def create_list(cls, id_: str, data: RichTextBlockList) -> RichTextBlock:
        """Create a list block
        """
        return cls.create_block(id_, RichTextBlockType.LIST, data)

    @classmethod
    def create_timestamp(cls, id_: str, data: RichTextBlockTimestamp) -> RichTextBlock:
        """Create a timestamp block
        """
        return cls.create_block(id_, RichTextBlockType.TIMESTAMP, data)

    @classmethod
    def create_formula(cls, id_: str, formula: str) -> RichTextBlock:
        """_summary_

        :param id_: id of the block
        :type id_: str
        :param formula: math formula using the KaTeX syntax
        :type formula: str
        :return: block
        :rtype: RichTextBlock
        """
        data: RichTextBlockFormula = RichTextBlockFormula(
            formula=formula
        )
        return cls.create_block(id_, RichTextBlockType.FORMULA, data)

    @classmethod
    def create_block(cls, id_: str, block_type: RichTextBlockType, data: RichTextBlockDataBase) -> RichTextBlock:
        """Create a block
        """
        if not data:
            raise ValueError('The data is empty')
        if not isinstance(data, RichTextBlockDataBase):
            raise ValueError('The data is not valid; it should be a RichTextBlockDataBase')
        return RichTextBlock(
            id=id_,
            type=block_type,
            data=data.to_json_dict(),
        )

    @classmethod
    def create_rich_text_dto(cls, blocks: List[RichTextBlock]) -> RichTextDTO:
        return RichTextDTO(
            blocks=blocks,
            version=RichText.CURRENT_VERION,
            editorVersion=RichText.CURRENT_EDITOR_VERSION,
        )

    @classmethod
    def from_json(cls, data: dict) -> 'RichText':
        return RichText(RichTextDTO.from_json(data))

    @classmethod
    def is_rich_text_json(cls, data: dict) -> bool:
        """Check if the given data is a valid rich text json

        :param data: json object
        :type data: dict
        :return: True if the data is a valid rich text json, False otherwise
        :rtype: bool
        """
        if 'version' not in data or 'editorVersion' not in data or 'blocks' not in data:
            return False
        try:
            RichTextDTO.from_json(data)
            return True
        except Exception:
            return False

    @classmethod
    def from_json_file(cls, file_path: str) -> 'RichText':
        with open(file_path, 'r', encoding='utf-8') as file:
            rich_text_dto = RichTextDTO.from_json_str(file.read())
            return RichText(rich_text_dto)
