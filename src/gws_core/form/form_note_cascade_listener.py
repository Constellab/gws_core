from gws_core.form.form import Form
from gws_core.model.event.event import Event
from gws_core.model.event.event_listener import EventListener
from gws_core.model.event.event_listener_decorator import event_listener
from gws_core.note.note_events import NoteDeletedEvent
from gws_core.note.note_form_model import NoteFormModel


@event_listener
class FormNoteCascadeListener(EventListener):
    """Cascade-delete owned Forms when their owner Note is deleted, per
    spec §5.6.

    For each FORM block in the deleted note that carries is_owner=True:
    if no other Note still references the same form_id, the Form is
    deleted; otherwise it is preserved (orphaned-of-owner is allowed).

    Runs synchronously inside the note-delete transaction. If a Form
    delete fails, the surrounding note delete rolls back too.

    The listener fires BEFORE note.delete_instance() (per the
    NoteDeletedEvent contract), so the deleting note's NoteFormModel rows
    still exist at this moment — the "other refs" query filters them out
    explicitly via NoteFormModel.has_other_references.
    """

    def is_synchronous(self) -> bool:
        return True

    def handle(self, event: Event) -> None:
        if not isinstance(event, NoteDeletedEvent):
            return

        owner_rows = NoteFormModel.get_owners_of_note(event.note_id)
        for row in owner_rows:
            form_id = row.form_id
            if NoteFormModel.has_other_references(form_id, event.note_id):
                continue
            form = Form.get_by_id(form_id)
            if form is None:
                continue
            # Drop the deleting note's join row first so the Form's
            # RESTRICT FK doesn't block the delete. CASCADE on the note
            # FK would do this automatically once note.delete_instance()
            # runs, but that's after this listener returns.
            row.delete_instance()
            form.delete_instance()
