from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .event import Event


class EventListener(ABC):
    """Abstract base class for event listeners.

    Event listeners receive all events and decide internally which ones to handle.
    Implement the `handle` method to filter and process events.

    Listeners can be synchronous or asynchronous:
    - Synchronous (is_synchronous() returns True):
      Runs in the caller's thread, same DB transaction.
      Exceptions propagate to the caller (can rollback transactions).
      Runs BEFORE async listeners.
    - Asynchronous (default, is_synchronous() returns False):
      Runs in background worker thread.
      Exceptions are caught and logged.
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

    def is_synchronous(self) -> bool:
        """Whether this listener runs synchronously in the caller's thread.

        If True:
        - Executes in the caller's thread (same DB transaction)
        - Exceptions propagate to the caller (can rollback transactions)
        - Runs BEFORE async listeners

        If False (default):
        - Executes in background worker thread
        - Exceptions are caught and logged

        :return: True for synchronous execution, False for async (default)
        :rtype: bool
        """
        return False
