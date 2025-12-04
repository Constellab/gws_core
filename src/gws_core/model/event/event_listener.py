from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .event import Event


class EventListener(ABC):
    """Abstract base class for event listeners.

    Event listeners receive all events and decide internally which ones to handle.
    Implement the `handle` method to filter and process events.

    Example:
        class UserAuditListener(EventListener):
            def handle(self, event: Event) -> None:
                # Filter events in the handle method using discriminated unions
                if event.entity_type == 'user':
                    if event.action == 'created':
                        user = event.entity  # Type checker knows it's User
                        Logger.info(f"User created: {user.email}")
                    elif event.action == 'activated':
                        user = event.entity
                        Logger.info(f"User activated: {user.email}")
    """

    @abstractmethod
    def handle(self, event: Event) -> None:
        """Handle the event.

        This method is called for all events. Implement filtering logic
        inside this method to handle only the events you're interested in.

        Use the discriminated union pattern (entity_type + action) to
        filter and get type-safe access to event properties.

        :param event: The event to handle
        :type event: Event
        """
        pass
