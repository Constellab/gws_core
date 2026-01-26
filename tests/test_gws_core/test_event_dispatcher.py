"""Tests for EventDispatcher sync/async listener routing."""

from dataclasses import dataclass
from typing import Literal
import time

from gws_core.model.event.base_event import BaseEvent
from gws_core.model.event.event_dispatcher import EventDispatcher
from gws_core.model.event.event_listener import EventListener
from gws_core.test.base_test_case import BaseTestCase


@dataclass
class TestEvent(BaseEvent):
    type: Literal["test"] = "test"
    action: Literal["run"] = "run"


class TestEventDispatcher(BaseTestCase):

    def setUp(self):
        """Clear listeners before each test."""
        EventDispatcher.get_instance().clear_listeners()

    def tearDown(self):
        """Clear listeners after each test."""
        EventDispatcher.get_instance().clear_listeners()

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
        dispatcher.dispatch(TestEvent())

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
            dispatcher.dispatch(TestEvent())
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
        dispatcher.dispatch(TestEvent())

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
        dispatcher.dispatch(TestEvent())

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
