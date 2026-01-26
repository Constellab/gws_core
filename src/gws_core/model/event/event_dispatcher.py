from __future__ import annotations

from queue import Empty, Queue
from threading import Lock, Thread
from typing import TYPE_CHECKING

from gws_core.core.db.thread_db import ThreadDb
from gws_core.core.utils.logger import Logger

from .base_event import BaseEvent
from .event_listener import EventListener

if TYPE_CHECKING:
    from .event import Event


class EventDispatcher:
    """Central event dispatcher for the application.

    This is a singleton service that manages event listeners and dispatches events
    to them. Events are dispatched asynchronously using a single worker thread
    that processes events from a queue, avoiding the overhead of creating new
    threads for each event.

    Usage:
        # Register a listener
        dispatcher = EventDispatcher.get_instance()
        dispatcher.register(MyListener())

        # Dispatch an event
        event = UserCreatedEvent(entity=user, triggered_by=current_user)
        dispatcher.dispatch(event)

        # Unregister a listener
        dispatcher.unregister(listener)
    """

    _instance: EventDispatcher | None = None
    _lock: Lock = Lock()
    _listeners: list[EventListener] = []
    _listeners_lock: Lock = Lock()
    _event_queue: Queue
    _worker_thread: Thread
    _running: bool = False

    def __init__(self):
        """Private constructor. Use get_instance() instead."""
        self._listeners = []
        self._event_queue = Queue()
        self._running = True

        # Start single worker thread that will process all events
        self._worker_thread = ThreadDb(target=self._worker_loop, daemon=True)
        self._worker_thread.start()
        Logger.debug("EventDispatcher worker thread started")

    @classmethod
    def get_instance(cls) -> EventDispatcher:
        """Get the singleton instance of the EventDispatcher.

        :return: The EventDispatcher instance
        :rtype: EventDispatcher
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def register(self, listener: EventListener) -> None:
        """Register an event listener.

        :param listener: The listener to register
        :type listener: EventListener
        """
        if not isinstance(listener, EventListener):
            raise ValueError("Listener must be an instance of EventListener")

        with self._listeners_lock:
            if listener not in self._listeners:
                self._listeners.append(listener)
                Logger.debug(f"Registered event listener: {listener.__class__.__name__}")

    def unregister(self, listener: EventListener) -> None:
        """Unregister an event listener.

        :param listener: The listener to unregister
        :type listener: EventListener
        """
        with self._listeners_lock:
            if listener in self._listeners:
                self._listeners.remove(listener)
                Logger.debug(f"Unregistered event listener: {listener.__class__.__name__}")

    def dispatch(self, event: Event) -> None:
        """Dispatch an event to all registered listeners.

        Synchronous listeners (is_synchronous() == True) are called immediately
        in the caller's thread. Exceptions propagate to the caller.

        Asynchronous listeners (is_synchronous() == False) are queued for the
        background worker thread. Exceptions are caught and logged.

        Sync listeners always run BEFORE async listeners are queued.

        :param event: The event to dispatch
        :type event: Event
        """
        if not isinstance(event, BaseEvent):
            raise ValueError("Event must be an instance of BaseEvent")

        listeners = self._get_all_listeners()

        if not listeners:
            Logger.debug(f"No listeners registered for event: {event.get_event_name()}")
            return

        sync_listeners = [listener for listener in listeners if listener.is_synchronous()]
        async_listeners = [listener for listener in listeners if not listener.is_synchronous()]

        # Sync listeners: run in caller's thread, exceptions propagate
        if sync_listeners:
            self._notify_sync_listeners(event, sync_listeners)

        # Async listeners: queue for worker thread
        if async_listeners:
            self._event_queue.put((event, async_listeners))

    def _get_all_listeners(self) -> list[EventListener]:
        """Get all registered listeners.

        :return: List of all listeners
        :rtype: List[EventListener]
        """
        with self._listeners_lock:
            return self._listeners.copy()

    def _worker_loop(self) -> None:
        """Worker thread loop that processes events from the queue.

        This method runs continuously in a background thread, processing
        events as they are added to the queue.
        """
        Logger.debug("EventDispatcher worker thread running")

        while self._running:
            try:
                # Block for up to 1 second waiting for an event
                event, listeners = self._event_queue.get(timeout=1)
                self._notify_async_listeners(event, listeners)
                self._event_queue.task_done()
            except Empty:
                # Timeout - no events in queue, continue loop
                continue
            except Exception as e:
                Logger.error(f"Error in EventDispatcher worker loop: {e}", exception=e)

        Logger.debug("EventDispatcher worker thread stopped")

    def _notify_sync_listeners(self, event: Event, listeners: list[EventListener]) -> None:
        """Notify synchronous listeners in the caller's thread.

        Exceptions are NOT caught — they propagate to the caller.
        This allows sync listeners to abort/rollback the caller's operation.

        :param event: The event to notify
        :type event: Event
        :param listeners: The synchronous listeners to notify
        :type listeners: list[EventListener]
        """
        event_name = event.get_event_name()
        Logger.debug(f"Dispatching event (sync): {event_name} to {len(listeners)} listener(s)")

        for listener in listeners:
            listener.handle(event)

    def _notify_async_listeners(self, event: Event, listeners: list[EventListener]) -> None:
        """Notify asynchronous listeners of an event.

        This method is called in a background thread. Each listener is called and errors are caught and logged.

        :param event: The event to notify
        :type event: Event
        :param listeners: The listeners to notify
        :type listeners: list[EventListener]
        """
        event_name = event.get_event_name()
        Logger.debug(f"Dispatching event (async): {event_name} to {len(listeners)} listener(s)")

        for listener in listeners:
            try:
                listener.handle(event)
            except Exception as e:
                Logger.error(
                    f"Error in event listener {listener.__class__.__name__} "
                    f"for event {event_name}: {e}",
                    exception=e,
                )

    def get_registered_listeners(self) -> list[EventListener]:
        """Get all registered listeners.

        :return: List of registered listeners
        :rtype: List[EventListener]
        """
        with self._listeners_lock:
            return self._listeners.copy()

    def clear_listeners(self) -> None:
        """Remove all registered listeners.

        This is useful for testing or resetting the dispatcher.
        """
        with self._listeners_lock:
            self._listeners.clear()
            Logger.info("Cleared all event listeners")

    def shutdown(self) -> None:
        """Shutdown the worker thread gracefully.

        This method should be called when the application is shutting down.
        It waits for all pending events in the queue to be processed before stopping.
        """
        Logger.info("Shutting down EventDispatcher...")

        # Stop accepting new events
        self._running = False

        # Wait for queue to be empty
        self._event_queue.join()

        # Wait for worker thread to finish
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5)

        Logger.info("EventDispatcher shut down complete")
