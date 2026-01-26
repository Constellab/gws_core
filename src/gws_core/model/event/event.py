from __future__ import annotations

from typing import TYPE_CHECKING, TypeAlias, Union

if TYPE_CHECKING:
    from gws_core.lab.system_event import SystemEvent
    from gws_core.note.note_events import NoteEvent
    from gws_core.user.user_events import UserEvent

# Global Event type that combines all event types in the system
# Currently only UserEvent, but can be extended:
# Event = UserEvent | ExperimentEvent | ProjectEvent | ...
Event: TypeAlias = Union["UserEvent", "SystemEvent", "NoteEvent"]
