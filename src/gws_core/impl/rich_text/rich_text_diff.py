from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.impl.rich_text.rich_text_types import RichTextBlock


class RichTextBlockAdded(BaseModelDTO):
    """Represents a block that exists in the new version but not in the old one."""
    block: RichTextBlock
    index: int


class RichTextBlockDeleted(BaseModelDTO):
    """Represents a block that exists in the old version but not in the new one."""
    block: RichTextBlock
    index: int


class RichTextBlockModified(BaseModelDTO):
    """Represents a block that exists in both versions but with changed data."""
    block_id: str
    old_block: RichTextBlock
    new_block: RichTextBlock
    old_index: int
    new_index: int


class RichTextDiff(BaseModelDTO):
    """Result of comparing two RichText documents.

    Contains the lists of added, deleted, and modified blocks.
    A block is matched between old and new by its id.
    If a block's id is present in both but the type changed, it is treated as deleted + added.
    """
    added: list[RichTextBlockAdded]
    deleted: list[RichTextBlockDeleted]
    modified: list[RichTextBlockModified]

    def has_changes(self) -> bool:
        """Return True if there are any differences."""
        return bool(self.added or self.deleted or self.modified)
