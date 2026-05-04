from gws_core.impl.rich_text.block.rich_text_block import (
    RichTextBlockDataBase,
    RichTextBlockTypeStandard,
)
from gws_core.impl.rich_text.block.rich_text_block_decorator import rich_text_block_decorator


@rich_text_block_decorator(RichTextBlockTypeStandard.FORM_TEMPLATE.value)
class RichTextBlockFormTemplate(RichTextBlockDataBase):
    """Embeds a reference to a published FormTemplateVersion in a NoteTemplate.

    At Note instantiation time (Phase 7), this block is replaced by a FORM
    block carrying a freshly-created Form bound to this version.
    """

    form_template_id: str
    form_template_version_id: str
    display_name: str | None = None

    def to_markdown(self) -> str:
        return f"[Form Template: {self.display_name or self.form_template_id}]"
