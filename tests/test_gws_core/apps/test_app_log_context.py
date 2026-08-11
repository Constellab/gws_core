import json
import logging
import time
from unittest import TestCase

from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import BasicMessageObserver
from gws_core.core.utils.app_log_context import AppLogContext
from gws_core.core.utils.logger import JSONFormatter, LogContext
from gws_core.core.utils.settings import Settings
from gws_core.impl.shell.shell_proxy import ShellProxy


# test_app_log_context
class TestAppLogContext(TestCase):
    """Attribution of MAIN-context log records to an app id (issue #103)."""

    def tearDown(self) -> None:
        AppLogContext.clear()

    def _format_record(self, formatter: JSONFormatter) -> dict:
        record = logging.LogRecord(
            name="gws", level=logging.INFO, pathname=__file__, lineno=1,
            msg="hello", args=None, exc_info=None,
        )
        return json.loads(formatter.format(record))

    def test_formatter_uses_app_context(self):
        formatter = JSONFormatter(context=LogContext.MAIN)

        # without app context: no context_id
        line = self._format_record(formatter)
        self.assertIsNone(line.get("context_id"))

        # with app context: the record carries the app id
        with AppLogContext.use("my-app-id"):
            line = self._format_record(formatter)
        self.assertEqual(line.get("context_id"), "my-app-id")

        # a formatter built with a fixed context_id (child app process) is not overridden
        fixed = JSONFormatter(context=LogContext.REFLEX, context_id="fixed-id")
        with AppLogContext.use("my-app-id"):
            line = self._format_record(fixed)
        self.assertEqual(line.get("context_id"), "fixed-id")

    def test_dispatcher_stamps_messages_at_notify_time(self):
        """The context is captured when the message is notified, not when the (timer
        thread) dispatch runs."""
        dispatcher = MessageDispatcher(interval_time_dispatched_buffer=0)
        observer = BasicMessageObserver()
        dispatcher.attach(observer)

        with AppLogContext.use("app-abc"):
            dispatcher.notify_info_message("from app operation")
        dispatcher.notify_info_message("outside")

        self.assertEqual(observer.messages[0].context_id, "app-abc")
        self.assertIsNone(observer.messages[1].context_id)

    def test_shell_proxy_output_carries_app_context(self):
        """Output read by the ShellProxy background thread keeps the app context."""
        proxy = ShellProxy(working_dir=Settings.make_temp_dir())
        observer = BasicMessageObserver()
        proxy.attach_observer(observer)

        with AppLogContext.use("app-shell"):
            sys_proc = proxy.run_in_new_thread(["echo", "hello-from-child"], dispatch_stdout=True)

        sys_proc.wait()
        # let the reader thread drain the pipe, then force the buffered dispatch
        deadline = time.time() + 5
        while time.time() < deadline:
            proxy.dispatch_waiting_messages()
            if any("hello-from-child" in message.message for message in observer.messages):
                break
            time.sleep(0.1)

        output_messages = [
            message for message in observer.messages if "hello-from-child" in message.message
        ]
        self.assertTrue(output_messages, "child output was never dispatched")
        self.assertEqual(output_messages[0].context_id, "app-shell")
        # the output line is tagged with the child pid
        self.assertIn(f"[pid {sys_proc.get_process().pid}]", output_messages[0].message)
