from gws_core.impl.rich_text.block.rich_text_block import (
    RichTextBlockDataBase,
    RichTextBlockTypeStandard,
)
from gws_core.impl.rich_text.block.rich_text_block_decorator import rich_text_block_decorator


@rich_text_block_decorator(RichTextBlockTypeStandard.FORM.value)
class RichTextBlockForm(RichTextBlockDataBase):
    """Embeds a Form (filled or being filled) in a Note.

    is_owner=True: this Note created the Form (Phase 7 cascade applies on note
    delete). is_owner=False: this Note references a Form created elsewhere;
    multiple notes may reference the same Form, and edits are visible to all.
    """

    form_id: str
    is_owner: bool
    display_name: str | None = None

    def to_markdown(self) -> str:
        return f"[Form: {self.display_name or self.form_id}]"
