from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockTypeStandard
from gws_core.impl.rich_text.block.rich_text_block_form_template import (
    RichTextBlockFormTemplate,
)
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.model.event.event import Event
from gws_core.model.event.event_listener import EventListener
from gws_core.model.event.event_listener_decorator import event_listener
from gws_core.note_template.note_template_events import (
    NoteTemplateContentUpdatedEvent,
)
from gws_core.note_template.note_template_form_template_model import (
    NoteTemplateFormTemplateModel,
)


@event_listener
class NoteTemplateFormTemplateJoinListener(EventListener):
    """Reconcile NoteTemplateFormTemplateModel rows whenever a NoteTemplate's
    content changes.

    Mirror of NoteFormJoinListener for the template side. Synchronous so
    reconciliation runs in the caller's transaction.
    """

    def is_synchronous(self) -> bool:
        return True

    def handle(self, event: Event) -> None:
        if not isinstance(event, NoteTemplateContentUpdatedEvent):
            return

        existing_version_ids = {
            row.form_template_version_id
            for row in NoteTemplateFormTemplateModel.get_by_note_template(
                event.note_template_id
            )
        }
        target = _form_template_blocks_to_join_state(event.new_content)

        for version_id in existing_version_ids - target.keys():
            NoteTemplateFormTemplateModel.delete_for(
                event.note_template_id, version_id
            )

        for version_id, template_id in target.items():
            NoteTemplateFormTemplateModel.upsert(
                event.note_template_id, version_id, template_id
            )


def _form_template_blocks_to_join_state(
    content: RichTextDTO | None,
) -> dict[str, str]:
    """Return {form_template_version_id: form_template_id} from FORM_TEMPLATE
    blocks in content. The block payload carries both ids; the join row
    stores both for cheap family-level queries.

    If a block carries a stale form_template_id (doesn't match the
    version's actual template_id), the version row wins — the join's
    denormalization must be consistent with the FK join.
    """
    if content is None:
        return {}
    rich_text = RichText(content)
    result: dict[str, str] = {}
    for block in rich_text.get_blocks_by_type(
        RichTextBlockTypeStandard.FORM_TEMPLATE
    ):
        data: RichTextBlockFormTemplate = block.get_data()
        if data.form_template_version_id in result:
            continue
        version = FormTemplateVersion.get_by_id(data.form_template_version_id)
        if version is None:
            # Stale block — skip rather than fail. The validator should
            # catch this on the next content edit.
            continue
        result[data.form_template_version_id] = version.template_id
    return result
