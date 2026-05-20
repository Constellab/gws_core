from gws_core.form.form import Form
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockTypeStandard
from gws_core.impl.rich_text.block.rich_text_block_form import RichTextBlockForm
from gws_core.impl.rich_text.block.rich_text_block_form_template import (
    RichTextBlockFormTemplate,
)
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextBlock, RichTextDTO


class NoteContentConverter:
    """Convert a Note's rich-text content into NoteTemplate-ready content.

    Reverse of NoteTemplateContentConverter: applies every content-level
    transformation needed when a Note is turned into a NoteTemplate. The
    NoteTemplateService.create_from_note path funnels through this converter
    so the transforms stay consistent.

    Today it handles one transform: FORM -> FORM_TEMPLATE. A FORM block
    embeds a filled Form; the resulting FORM_TEMPLATE block references the
    FormTemplate family that Form was created from (unpinned: no version).
    Adding a new transform means appending a private
    `_convert_<block_type>_blocks(rich_text)` method and dispatching to it
    from `convert`.

    The converter operates purely on rich-text content (no file-storage
    side effects, no DB writes).
    """

    @classmethod
    def convert(cls, content: RichTextDTO | None) -> RichTextDTO | None:
        """Apply every Note-to-NoteTemplate content transformation in
        order. Returns the converted content, or the input unchanged if
        no transforms apply.
        """
        if content is None:
            return None

        rich_text = RichText(content)
        cls._convert_form_blocks(rich_text)
        return rich_text.to_dto()

    # ------------------------------------------------------------------ #
    # Transforms — one private method per block-type rewrite.
    # ------------------------------------------------------------------ #

    @classmethod
    def _convert_form_blocks(cls, rich_text: RichText) -> None:
        """Replace each FORM block with an unpinned FORM_TEMPLATE block
        referencing the Form's FormTemplate. FORM blocks whose Form (or
        its FormTemplateVersion) can no longer be resolved are dropped.

        Idempotent on already-converted content: a NoteTemplate's content
        cannot carry FORM blocks (the validator forbids it), so calling
        this on NoteTemplate content is a no-op.
        """
        form_blocks = rich_text.get_blocks_by_type(RichTextBlockTypeStandard.FORM)
        for block in form_blocks:
            form_data: RichTextBlockForm = block.get_data()
            form_template_id = cls._resolve_form_template_id(form_data.form_id)
            if form_template_id is None:
                rich_text.remove_block_by_id(block.id)
                continue
            ft_block = RichTextBlock.from_data(
                RichTextBlockFormTemplate(
                    form_template_id=form_template_id,
                    form_template_version_id=None,
                ),
                id_=block.id,
            )
            rich_text.replace_block_by_id(block.id, ft_block)

    @classmethod
    def _resolve_form_template_id(cls, form_id: str) -> str | None:
        """Return the FormTemplate id behind a FORM block's Form, or None
        if the Form or its FormTemplateVersion no longer exists."""
        form = Form.get_by_id(form_id)
        if form is None:
            return None
        version = FormTemplateVersion.get_by_id(form.template_version_id)
        if version is None:
            return None
        return version.template_id
