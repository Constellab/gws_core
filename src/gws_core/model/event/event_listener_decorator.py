from typing import TypeVar

from gws_core.core.utils.logger import Logger

from .event_dispatcher import EventDispatcher
from .event_listener import EventListener

T = TypeVar("T", bound=EventListener)


def event_listener(cls: type[T]) -> type[T]:
    """Decorator that automatically registers an EventListener class.

    This decorator should be applied to classes that inherit from EventListener.
    When the class is defined (at import time), an instance is created and
    automatically registered with the EventDispatcher singleton.

    Listeners can control their execution mode by overriding ``is_synchronous()``:

    - **Asynchronous** (default): the listener runs in a background worker
      thread. Exceptions are caught and logged without affecting the caller.
    - **Synchronous** (``is_synchronous()`` returns ``True``): the listener
      runs in the caller's thread and within the same DB transaction.
      Exceptions propagate to the caller, which allows rolling back the
      transaction. Sync listeners always execute **before** async listeners.

    Example (async listener — default):
        @event_listener
        class UserAuditListener(EventListener):
            def handle(self, event: Event) -> None:
                if event.entity_type == 'user':
                    Logger.info(f"User event: {event.action}")

    Example (sync listener):
        @event_listener
        class NoteActivitySyncListener(EventListener):
            def is_synchronous(self) -> bool:
                return True

            def handle(self, event: Event) -> None:
                # Runs in the caller's thread; exceptions rollback the transaction.
                ...

    The listener is automatically registered when the module is imported.

    :param cls: The EventListener class to decorate
    :type cls: Type[EventListener]
    :return: The same class (unmodified)
    :rtype: Type[EventListener]
    :raises ValueError: If the class does not inherit from EventListener
    """
    if not issubclass(cls, EventListener):
        raise ValueError(
            f"@event_listener can only be applied to classes that inherit from EventListener. "
            f"{cls.__name__} does not inherit from EventListener."
        )

    try:
        # Create an instance of the listener
        listener_instance = cls()

        # Register it with the dispatcher
        EventDispatcher.get_instance().register(listener_instance)
    except Exception as e:
        Logger.error(f"Failed to auto-register event listener {cls.__name__}: {e}", exception=e)
        raise

    # Return the class unmodified
    return cls
