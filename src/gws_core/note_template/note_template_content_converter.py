from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.form.form_dto import CreateFormDTO
from gws_core.form.form_service import FormService
from gws_core.form_template.form_template_dto import FormTemplateVersionStatus
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockTypeStandard
from gws_core.impl.rich_text.block.rich_text_block_form import RichTextBlockForm
from gws_core.impl.rich_text.block.rich_text_block_form_template import (
    RichTextBlockFormTemplate,
)
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextBlock, RichTextDTO


class NoteTemplateContentConverter:
    """Convert a NoteTemplate's rich-text content into Note-ready content.

    Single home for every content-level transformation that has to happen
    when a NoteTemplate is materialized into (or merged into) a Note. The
    NoteService instantiation paths funnel through this converter so the
    transforms stay consistent across `NoteService.create(template_id=...)`
    and `NoteService.insert_template(...)`.

    Today the converter handles one transform: `FORM_TEMPLATE` → `FORM`
    blocks owning fresh `Form` rows (spec §5.4). Adding a new transform
    means appending a private `_convert_<block_type>_blocks(rich_text)`
    method and dispatching to it from `convert`.

    The converter operates purely on rich-text content (no file-storage
    side effects, no DB writes other than the Forms it creates as part of
    the FORM_TEMPLATE conversion). File-storage copies (e.g.
    `RichTextFileService.copy_object_dir`) stay at the NoteService call
    sites because their ordering relative to validation differs by path.
    """

    @classmethod
    def convert(cls, content: RichTextDTO | None) -> RichTextDTO | None:
        """Apply every NoteTemplate-to-Note content transformation in
        order. Returns the converted content, or the input unchanged if
        no transforms apply.

        :raises BadRequestException: if any transform cannot complete
            (e.g. an archived FORM_TEMPLATE pin with no published fallback).
        """
        if content is None:
            return None

        rich_text = RichText(content)
        cls._convert_form_template_blocks(rich_text)
        return rich_text.to_dto()

    # ------------------------------------------------------------------ #
    # Transforms — one private method per block-type rewrite.
    # ------------------------------------------------------------------ #

    @classmethod
    def _convert_form_template_blocks(cls, rich_text: RichText) -> None:
        """Replace each FORM_TEMPLATE block with a FORM block owning a
        freshly-created Form (spec §5.4). Other blocks pass through.

        Idempotent on already-converted content: a Note's content cannot
        carry FORM_TEMPLATE blocks (the validator forbids it), so calling
        this on Note content is a no-op.
        """
        ft_blocks = rich_text.get_blocks_by_type(
            RichTextBlockTypeStandard.FORM_TEMPLATE
        )
        for block in ft_blocks:
            ft_data: RichTextBlockFormTemplate = block.get_data()
            resolved_version = cls._resolve_form_template_version(ft_data)
            form = FormService.create(
                CreateFormDTO(template_version_id=resolved_version.id)
            )
            form_block = RichTextBlock.from_data(
                RichTextBlockForm(
                    form_id=form.id,
                    is_owner=True,
                    display_name=ft_data.display_name,
                ),
                id_=block.id,
            )
            rich_text.replace_block_by_id(block.id, form_block)

    @classmethod
    def _resolve_form_template_version(
        cls, ft_data: RichTextBlockFormTemplate
    ) -> FormTemplateVersion:
        """Return the version to bind a new Form to. Falls back to the
        template's current published version if the pinned one is
        ARCHIVED (spec §5.4 step 1.1)."""
        version = FormTemplateVersion.get_by_id(ft_data.form_template_version_id)
        if version is None:
            raise BadRequestException(
                "FORM_TEMPLATE block references unknown form template "
                f"version: {ft_data.form_template_version_id}"
            )
        if version.status == FormTemplateVersionStatus.PUBLISHED:
            return version
        if version.status == FormTemplateVersionStatus.ARCHIVED:
            fallback = FormTemplateVersion.get_current_published_version(
                ft_data.form_template_id
            )
            if fallback is None:
                raise BadRequestException(
                    "FORM_TEMPLATE block pins an ARCHIVED version "
                    f"({ft_data.form_template_version_id}) and the form "
                    f"template ({ft_data.form_template_id}) has no "
                    "current PUBLISHED version to fall back to. Cannot "
                    "instantiate."
                )
            return fallback
        raise BadRequestException(
            "FORM_TEMPLATE block references a version with unexpected "
            f"status {version.status.value}; expected PUBLISHED or ARCHIVED."
        )
