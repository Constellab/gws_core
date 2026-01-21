from typing import Any

from gws_core.impl.rich_text.block.rich_text_block import (
    RichTextBlockDataBase,
    RichTextBlockTypeStandard,
)
from gws_core.impl.rich_text.block.rich_text_block_decorator import rich_text_block_decorator


@rich_text_block_decorator(RichTextBlockTypeStandard.RESOURCE_VIEW.value)
class RichTextBlockResourceView(RichTextBlockDataBase):
    """Object representing a resource view in a rich text"""

    id: str
    view_config_id: str
    resource_id: str
    scenario_id: str | None = None
    view_method_name: str
    view_config: dict[str, Any]
    title: str | None = None
    caption: str | None = None

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


@rich_text_block_decorator(RichTextBlockTypeStandard.NOTE_RESOURCE_VIEW.value)
class RichTextBlockNoteResourceView(RichTextBlockDataBase):
    """Object representing a resource view in an note rich text"""

    id: str
    # key in the note of the sub resource to call view on
    sub_resource_key: str
    view_method_name: str
    view_config: dict[str, Any]
    title: str | None = None
    caption: str | None = None

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


@rich_text_block_decorator(RichTextBlockTypeStandard.FILE_VIEW.value)
class RichTextBlockViewFile(RichTextBlockDataBase):
    """Object representing a independant view in a rich text, the view is not associated with a resource"""

    id: str
    filename: str
    title: str | None = None
    caption: str | None = None

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
