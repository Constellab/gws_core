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

    Example:
        @event_listener
        class UserAuditListener(EventListener):
            def handle(self, event: Event) -> None:
                if event.entity_type == 'user':
                    Logger.info(f"User event: {event.action}")

            def get_priority(self) -> int:
                return 10

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
