from dataclasses import dataclass
from typing import Literal

from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.model.event.base_event import BaseEvent


@dataclass
class BaseNoteEvent(BaseEvent):
    """Base class for all note events."""
    type: Literal["note"] = "note"
    action: str = ""


@dataclass
class NoteContentUpdatedEvent(BaseNoteEvent):
    """Dispatched BEFORE saving note content in NoteService.update_content().

    Synchronous listeners can:
    - Mutate new_content (e.g., replace draft blocks with confirmed blocks)
    - Raise exceptions to abort the save (rollback the transaction)

    :param note_id: ID of the note being updated
    :param old_content: The current content before the update (may be None for new notes)
    :param new_content: The new content to be saved — MUTABLE by sync listeners
    """
    action: Literal["content_updated"] = "content_updated"
    note_id: str = ""
    old_content: RichTextDTO | None = None
    new_content: RichTextDTO | None = None


@dataclass
class NoteDeletedEvent(BaseNoteEvent):
    """Dispatched BEFORE deleting a note in NoteService._delete_note_db().

    Synchronous listeners can:
    - Clean up related data (e.g., reverse activities linked to the note)
    - Raise exceptions to abort the deletion (rollback the transaction)

    :param note_id: ID of the note being deleted
    :param content: The current note content before deletion
    """
    action: Literal["deleted"] = "deleted"
    note_id: str = ""
    content: RichTextDTO | None = None


NoteEvent = NoteContentUpdatedEvent | NoteDeletedEvent
