from gws_core.impl.rich_text.block.rich_text_block import RichTextBlockTypeStandard
from gws_core.impl.rich_text.block.rich_text_block_form import RichTextBlockForm
from gws_core.impl.rich_text.rich_text import RichText
from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.model.event.event import Event
from gws_core.model.event.event_listener import EventListener
from gws_core.model.event.event_listener_decorator import event_listener
from gws_core.note.note_events import NoteContentUpdatedEvent
from gws_core.note.note_form_model import NoteFormModel


@event_listener
class NoteFormJoinListener(EventListener):
    """Reconcile NoteFormModel rows whenever a Note's content changes.

    Synchronous so reconciliation runs in the caller's transaction; if the
    listener raises, the surrounding content update rolls back.

    The listener is the single owner of join-table writes for notes — the
    `note` module dispatches the event and remains unaware of the form
    module.
    """

    def is_synchronous(self) -> bool:
        return True

    def handle(self, event: Event) -> None:
        if not isinstance(event, NoteContentUpdatedEvent):
            return

        existing_form_ids = {
            row.form_id for row in NoteFormModel.get_by_note(event.note_id)
        }
        target = _form_blocks_to_join_state(event.new_content)

        for form_id in existing_form_ids - target.keys():
            NoteFormModel.delete_for(event.note_id, form_id)

        for form_id, is_owner in target.items():
            NoteFormModel.upsert(event.note_id, form_id, is_owner)


def _form_blocks_to_join_state(
    content: RichTextDTO | None,
) -> dict[str, bool]:
    """Return {form_id: is_owner} from FORM blocks in content. Multiple
    blocks for the same form_id collapse to one entry; if any block is an
    owner, the entry is True (avoids losing ownership info on collapse)."""
    if content is None:
        return {}
    rich_text = RichText(content)
    result: dict[str, bool] = {}
    for block in rich_text.get_blocks_by_type(RichTextBlockTypeStandard.FORM):
        data: RichTextBlockForm = block.get_data()
        if data.form_id in result:
            result[data.form_id] = result[data.form_id] or data.is_owner
        else:
            result[data.form_id] = data.is_owner
    return result
