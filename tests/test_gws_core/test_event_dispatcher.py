"""Tests for EventDispatcher sync/async listener routing."""

import time
from dataclasses import dataclass
from typing import Literal, cast

from gws_core.model.event.base_event import BaseEvent
from gws_core.model.event.event import Event
from gws_core.model.event.event_dispatcher import EventDispatcher
from gws_core.model.event.event_listener import EventListener
from gws_core.test.base_test_case import BaseTestCase


@dataclass
class EventTest(BaseEvent):
    type: Literal["test"] = "test"
    action: Literal["run"] = "run"


class TestEventDispatcher(BaseTestCase):

    def setUp(self):
        """Isolate the dispatcher: snapshot the app-wide listeners (registered
        once at brick import time and never re-registered), then start from a
        clean slate. Restored in tearDown so other test files on the same
        worker process still see them."""
        dispatcher = EventDispatcher.get_instance()
        self._saved_listeners = dispatcher.get_registered_listeners()
        dispatcher.clear_listeners()

    def tearDown(self):
        """Restore the app-wide listeners snapshotted in setUp."""
        dispatcher = EventDispatcher.get_instance()
        dispatcher.clear_listeners()
        for listener in self._saved_listeners:
            dispatcher.register(listener)

    def test_sync_listener_runs_in_caller_thread(self):
        """Sync listener should execute immediately in the caller's thread."""
        results = []

        class SyncListener(EventListener):
            def is_synchronous(self) -> bool:
                return True
            def handle(self, event) -> None:
                results.append("sync_handled")

        dispatcher = EventDispatcher.get_instance()
        dispatcher.register(SyncListener())
        dispatcher.dispatch(cast(Event, EventTest()))

        # Should be immediate — no need to wait
        self.assertEqual(results, ["sync_handled"])

    def test_sync_listener_exception_propagates(self):
        """Exception in sync listener should propagate to the caller."""

        class FailingSyncListener(EventListener):
            def is_synchronous(self) -> bool:
                return True
            def handle(self, event) -> None:
                raise ValueError("Sync listener error")

        dispatcher = EventDispatcher.get_instance()
        dispatcher.register(FailingSyncListener())

        with self.assertRaises(ValueError) as ctx:
            dispatcher.dispatch(cast(Event, EventTest()))
        self.assertIn("Sync listener error", str(ctx.exception))

    def test_async_listener_exception_does_not_propagate(self):
        """Exception in async listener should NOT propagate to the caller."""
        results = []

        class FailingAsyncListener(EventListener):
            def handle(self, event) -> None:
                raise ValueError("Async listener error")

        class SuccessAsyncListener(EventListener):
            def handle(self, event) -> None:
                results.append("success")

        dispatcher = EventDispatcher.get_instance()
        dispatcher.register(FailingAsyncListener())
        dispatcher.register(SuccessAsyncListener())

        # Should NOT raise
        dispatcher.dispatch(cast(Event, EventTest()))

        # Wait for async processing
        time.sleep(0.5)
        self.assertIn("success", results)

    def test_sync_runs_before_async(self):
        """Sync listeners should run before async listeners are queued."""
        order = []

        class SyncListener(EventListener):
            def is_synchronous(self) -> bool:
                return True
            def handle(self, event) -> None:
                order.append("sync")

        class AsyncListener(EventListener):
            def handle(self, event) -> None:
                order.append("async")

        dispatcher = EventDispatcher.get_instance()
        dispatcher.register(AsyncListener())
        dispatcher.register(SyncListener())
        dispatcher.dispatch(cast(Event, EventTest()))

        # Sync should already be in the list
        self.assertEqual(order[0], "sync")

        # Wait for async
        time.sleep(0.5)
        self.assertEqual(order, ["sync", "async"])

    def test_default_listener_is_async(self):
        """A listener that doesn't override is_synchronous() should be async."""

        class DefaultListener(EventListener):
            def handle(self, event) -> None:
                pass

        listener = DefaultListener()
        self.assertFalse(listener.is_synchronous())
