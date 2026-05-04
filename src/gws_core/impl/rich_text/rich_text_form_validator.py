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
from gws_core.impl.rich_text.rich_text_types import RichTextDTO


class RichTextFormBlockValidator:
    """Validates form-related rich text blocks against their host context.

    Two responsibilities:

    1. Context gating. FORM_TEMPLATE blocks are only valid in NoteTemplate
       content; FORM blocks are only valid in Note content. The wrong
       combination is rejected at content-update time.
    2. Reference validity. A FORM_TEMPLATE block must reference a PUBLISHED
       FormTemplateVersion at insertion time; a FORM block must reference an
       existing Form. To avoid breaking existing valid content when a target
       is later archived/deleted, reference validity is only enforced on
       blocks that are *newly introduced* in the new content (i.e., the
       block id was not present in the old content).
    """

    @classmethod
    def validate_for_note(
        cls,
        new_content: RichTextDTO,
        old_content: RichTextDTO | None = None,
    ) -> None:
        """Reject FORM_TEMPLATE blocks; reject newly-introduced FORM blocks
        whose form_id does not exist."""
        old_block_ids = cls._collect_block_ids(old_content)
        for block in new_content.blocks:
            if block.is_type(RichTextBlockTypeStandard.FORM_TEMPLATE):
                raise BadRequestException("FORM_TEMPLATE blocks are not allowed in Note content.")
            if block.is_type(RichTextBlockTypeStandard.FORM) and block.id not in old_block_ids:
                form_block: RichTextBlockForm = block.get_data()
                if Form.get_by_id(form_block.form_id) is None:
                    raise BadRequestException(
                        f"FORM block references unknown form_id: {form_block.form_id}"
                    )

    @classmethod
    def validate_for_note_template(
        cls,
        new_content: RichTextDTO,
        old_content: RichTextDTO | None = None,
    ) -> None:
        """Reject FORM blocks; reject newly-introduced FORM_TEMPLATE blocks
        whose pinned version is not PUBLISHED, or whose form_template_id does
        not match the version's actual template_id."""
        old_block_ids = cls._collect_block_ids(old_content)
        for block in new_content.blocks:
            if block.is_type(RichTextBlockTypeStandard.FORM):
                raise BadRequestException("FORM blocks are not allowed in NoteTemplate content.")
            if (
                block.is_type(RichTextBlockTypeStandard.FORM_TEMPLATE)
                and block.id not in old_block_ids
            ):
                ft_block: RichTextBlockFormTemplate = block.get_data()
                version = FormTemplateVersion.get_by_id(ft_block.form_template_version_id)
                if version is None:
                    raise BadRequestException(
                        f"FORM_TEMPLATE block references unknown version: "
                        f"{ft_block.form_template_version_id}"
                    )
                if version.status != FormTemplateVersionStatus.PUBLISHED:
                    raise BadRequestException(
                        "FORM_TEMPLATE block must reference a PUBLISHED "
                        f"version, but version "
                        f"{ft_block.form_template_version_id} has status "
                        f"{version.status.value}."
                    )
                if version.template_id != ft_block.form_template_id:
                    raise BadRequestException(
                        "FORM_TEMPLATE block form_template_id "
                        f"{ft_block.form_template_id} does not match the "
                        f"version's template_id {version.template_id}."
                    )

    @staticmethod
    def _collect_block_ids(content: RichTextDTO | None) -> set[str]:
        if content is None:
            return set()
        return {block.id for block in content.blocks}
