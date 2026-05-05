from dataclasses import dataclass
from typing import Literal

from gws_core.impl.rich_text.rich_text_types import RichTextDTO
from gws_core.model.event.base_event import BaseEvent


@dataclass
class BaseNoteTemplateEvent(BaseEvent):
    """Base class for all note-template events."""
    type: Literal["note_template"] = "note_template"
    action: str = ""


@dataclass
class NoteTemplateContentUpdatedEvent(BaseNoteTemplateEvent):
    """Dispatched BEFORE saving note-template content in
    NoteTemplateService.update_content().

    Synchronous listeners can:
    - Mutate new_content (e.g., reconcile or annotate blocks)
    - Raise exceptions to abort the save (rollback the transaction)

    :param note_template_id: ID of the note template being updated
    :param old_content: The current content before the update (may be None)
    :param new_content: The new content to be saved — MUTABLE by sync listeners
    """
    action: Literal["content_updated"] = "content_updated"
    note_template_id: str = ""
    old_content: RichTextDTO | None = None
    new_content: RichTextDTO | None = None


NoteTemplateEvent = NoteTemplateContentUpdatedEvent
