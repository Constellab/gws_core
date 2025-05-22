from typing import List, Literal

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.impl.rich_text.block.rich_text_block import (
    RichTextBlockDataBase, RichTextBlockType)


class RichTextBlockListItem(BaseModelDTO):
    """Object representing a list block data in a rich text

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    content: str
    items: List["RichTextBlockListItem"] = []

    def to_markdown(self, prefix="- ", indent="  ") -> str:
        """Convert the list item to markdown

        :param prefix: the prefix to use for the item, defaults to "- "
        :type prefix: str, optional
        :param indent: indentation to use for nested items, defaults to "  "
        :type indent: str, optional
        :return: the markdown representation of the list item
        :rtype: str
        """
        result = f"{prefix}{self.content}"

        if self.items and len(self.items) > 0:
            for item in self.items:
                result += f"\n{indent}{item.to_markdown(prefix, indent)}"

        return result


class RichTextBlockList(RichTextBlockDataBase):
    """Object representing a list block data in a rich text

    :param TypedDict: [description]
    :type TypedDict: [type]
    """
    style: Literal['ordered', 'unordered', 'checklist']
    items: List[RichTextBlockListItem]

    def to_markdown(self) -> str:
        """Convert the list to markdown

        :return: the markdown representation of the list
        :rtype: str
        """
        result = []
        for index, item in enumerate(self.items):
            if self.style == 'ordered':
                prefix = f"{index + 1}. "
            elif self.style == 'checklist':
                # Markdown checkbox syntax
                prefix = "- [ ] "
            else:
                prefix = "- "
            result.append(item.to_markdown(prefix=prefix))

        return "\n".join(result)

    def get_type(self) -> RichTextBlockType:
        """Get the type of the block

        :return: the type of the block
        :rtype: RichTextBlockType
        """
        return RichTextBlockType.LIST
