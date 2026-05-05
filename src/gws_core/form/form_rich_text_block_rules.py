"""Form-specific rules registered with the generic
`RichTextContentValidator`.

Two block types: `FORM` (only valid in Note content) and `FORM_TEMPLATE`
(only valid in NoteTemplate content). Both validate that newly-introduced
blocks reference real, status-appropriate targets. See spec §5.1, §5.3.
"""
from gws_core.core.exception.exceptions.bad_request_exception import (
    BadRequestException,
)
from gws_core.form.form import Form
from gws_core.form_template.form_template_dto import FormTemplateVersionStatus
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockTypeStandard
from gws_core.impl.rich_text.block.rich_text_block_form import RichTextBlockForm
from gws_core.impl.rich_text.block.rich_text_block_form_template import (
    RichTextBlockFormTemplate,
)
from gws_core.impl.rich_text.rich_text_content_validator import (
    RichTextBlockRule,
    RichTextContentValidator,
    RichTextHostContext,
)
from gws_core.impl.rich_text.rich_text_types import RichTextBlock


class FormBlockRule(RichTextBlockRule):
    """`FORM` blocks: only valid in Note content; newly-introduced blocks
    must reference an existing Form."""

    @property
    def block_type(self) -> RichTextBlockTypeStandard:
        return RichTextBlockTypeStandard.FORM

    def allowed_contexts(self) -> set[RichTextHostContext]:
        return {RichTextHostContext.NOTE}

    def validate_new_block(self, block: RichTextBlock) -> None:
        form_block: RichTextBlockForm = block.get_data()
        if Form.get_by_id(form_block.form_id) is None:
            raise BadRequestException(
                f"FORM block references unknown form_id: {form_block.form_id}"
            )


class FormTemplateBlockRule(RichTextBlockRule):
    """`FORM_TEMPLATE` blocks: only valid in NoteTemplate content;
    newly-introduced blocks must pin a PUBLISHED FormTemplateVersion whose
    template_id matches the block's payload."""

    @property
    def block_type(self) -> RichTextBlockTypeStandard:
        return RichTextBlockTypeStandard.FORM_TEMPLATE

    def allowed_contexts(self) -> set[RichTextHostContext]:
        return {RichTextHostContext.NOTE_TEMPLATE}

    def validate_new_block(self, block: RichTextBlock) -> None:
        ft_block: RichTextBlockFormTemplate = block.get_data()
        version = FormTemplateVersion.get_by_id(ft_block.form_template_version_id)
        if version is None:
            raise BadRequestException(
                "FORM_TEMPLATE block references unknown version: "
                f"{ft_block.form_template_version_id}"
            )
        if version.status != FormTemplateVersionStatus.PUBLISHED:
            raise BadRequestException(
                "FORM_TEMPLATE block must reference a PUBLISHED version, "
                f"but version {ft_block.form_template_version_id} has "
                f"status {version.status.value}."
            )
        if version.template_id != ft_block.form_template_id:
            raise BadRequestException(
                "FORM_TEMPLATE block form_template_id "
                f"{ft_block.form_template_id} does not match the version's "
                f"template_id {version.template_id}."
            )


# Registration runs at import time so a side-effect import from
# gws_core/__init__.py is enough to wire these up.
RichTextContentValidator.register(FormBlockRule())
RichTextContentValidator.register(FormTemplateBlockRule())
