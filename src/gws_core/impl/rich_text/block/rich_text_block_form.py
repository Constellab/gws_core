from enum import Enum

from gws_core.impl.rich_text.block.rich_text_block import (
    RichTextBlockDataBase,
    RichTextBlockTypeStandard,
)
from gws_core.impl.rich_text.block.rich_text_block_decorator import rich_text_block_decorator


class RichTextBlockFormDisplayMode(Enum):
    """Defines how a Form block is rendered inside a rich text note."""

    PREVIEW = "preview"
    FORM = "form"
    JSON = "json"
    TABLE = "table"


@rich_text_block_decorator(RichTextBlockTypeStandard.FORM.value)
class RichTextBlockForm(RichTextBlockDataBase):
    """Embeds a Form (filled or being filled) in a Note.

    is_owner=True: this Note created the Form (Phase 7 cascade applies on note
    delete). is_owner=False: this Note references a Form created elsewhere;
    multiple notes may reference the same Form, and edits are visible to all.
    """

    form_id: str
    is_owner: bool
    # when None, show preview mode in DRAFT and form mode in PUBLISHED; when set, override this default behavior
    display_mode: RichTextBlockFormDisplayMode | None = None

    def to_markdown(self) -> str:
        return f"[Form: {self.form_id}]"
