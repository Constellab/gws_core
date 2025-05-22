from typing import Any, Dict, Optional

from gws_core.impl.rich_text.block.rich_text_block import (
    RichTextBlockDataBase, RichTextBlockType)


class RichTextBlockResourceView(RichTextBlockDataBase):
    """Object representing a resource view in a rich text"""
    id: str
    view_config_id: str
    resource_id: str
    scenario_id: Optional[str] = None
    view_method_name: str
    view_config: Dict[str, Any]
    title: Optional[str] = None
    caption: Optional[str] = None

    def to_markdown(self) -> str:
        """Convert the resource view to markdown

        :return: the markdown representation of the resource view
        :rtype: str
        """
        result = f"**Resource View**: {self.title or 'Untitled'}"
        if self.caption:
            result += f"\n*{self.caption}*"
        result += f"\n(Resource ID: {self.resource_id}, View Method: {self.view_method_name})"
        return result

    def get_type(self) -> RichTextBlockType:
        return RichTextBlockType.RESOURCE_VIEW


class RichTextBlockNoteResourceView(RichTextBlockDataBase):
    """Object representing a resource view in an note rich text"""
    id: str
    # key in the note of the sub resource to call view on
    sub_resource_key: str
    view_method_name: str
    view_config: Dict[str, Any]
    title: Optional[str] = None
    caption: Optional[str] = None

    def to_markdown(self) -> str:
        """Convert the note resource view to markdown

        :return: the markdown representation of the note resource view
        :rtype: str
        """
        result = f"**Note Resource View**: {self.title or 'Untitled'}"
        if self.caption:
            result += f"\n*{self.caption}*"
        result += f"\n(Resource Key: {self.sub_resource_key}, View Method: {self.view_method_name})"
        return result

    def get_type(self) -> RichTextBlockType:
        return RichTextBlockType.NOTE_RESOURCE_VIEW


class RichTextBlockViewFile(RichTextBlockDataBase):
    """Object representing a independant view in a rich text, the view is not associated with a resource"""
    id: str
    filename: str
    title: Optional[str] = None
    caption: Optional[str] = None

    def to_markdown(self) -> str:
        """Convert the file view to markdown

        :return: the markdown representation of the file view
        :rtype: str
        """
        result = f"**File View**: {self.title or self.filename}"
        if self.caption:
            result += f"\n*{self.caption}*"
        result += f"\n(File: {self.filename})"
        return result

    def get_type(self) -> RichTextBlockType:
        return RichTextBlockType.FILE_VIEW
