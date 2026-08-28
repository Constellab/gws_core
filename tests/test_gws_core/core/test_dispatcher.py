from time import sleep

from gws_core import BaseTestCase
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_level import MessageLevel
from gws_core.core.classes.observer.message_observer import BasicMessageObserver
from gws_core.progress_bar.progress_bar import ProgressBar


# test_dispatcher
class TestDispatcher(BaseTestCase):
    def test_dispatcher(self):
        dispatcher = MessageDispatcher(0.05, 0.25)

        observer = BasicMessageObserver()
        dispatcher.attach(observer)

        dispatcher.notify_info_message("message 1")
        sleep(0.30)
        self.assertEqual(len(observer.messages), 1)
        self.assertEqual(observer.messages[0].message, "message 1")
        self.assertEqual(observer.messages[0].status, "INFO")

        # check that multiple messages are merged
        dispatcher.notify_info_message("message 2")
        dispatcher.notify_info_message("message 3")
        sleep(0.30)
        self.assertEqual(len(observer.messages), 2)
        self.assertEqual(observer.messages[1].message, "message 2\nmessage 3")

        # check that slower messages are not merge but dispatched 1 time
        dispatcher.notify_info_message("message 4")
        self.assertEqual(len(observer.messages), 2)
        sleep(0.10)
        dispatcher.notify_info_message("message 5")
        sleep(0.30)
        self.assertEqual(len(observer.messages), 4)
        self.assertEqual(observer.messages[2].message, "message 4")
        self.assertEqual(observer.messages[3].message, "message 5")

        # test direct dispatch
        dispatcher.notify_info_message("message 6")
        dispatcher.force_dispatch_waiting_messages()
        self.assertEqual(len(observer.messages), 5)
        self.assertEqual(observer.messages[4].message, "message 6")

    def test_dispatcher_with_progress_bar(self):
        dispatcher = MessageDispatcher(0.05, 0.25)

        try:
            progress_bar = ProgressBar()
            dispatcher.attach_progress_bar(progress_bar)

            dispatcher.notify_info_message("message 1")
            sleep(0.30)

            self.assertEqual(len(progress_bar.get_messages()), 1)
            self.assertEqual(progress_bar.get_messages()[0].text, "message 1")
        except Exception as err:
            dispatcher.force_dispatch_waiting_messages()
            raise err

    def test_level(self):
        dispatcher = MessageDispatcher(0, 0)

        observer = BasicMessageObserver()
        dispatcher.attach(observer)

        dispatcher.notify_debug_message("message 1")
        self.assertEqual(len(observer.messages), 0)

        dispatcher.notify_info_message("message 1")
        self.assertEqual(len(observer.messages), 1)

    def _assert_dispatched_message(
        self,
        observer: BasicMessageObserver,
        expected_count: int,
        message: str,
        status: str,
        progress: float | None = None,
    ) -> None:
        """Check the number of dispatched messages and the content of the last one.

        :param observer: the observer attached to the dispatcher
        :param expected_count: expected total number of dispatched messages
        :param message: expected message text of the last dispatched message
        :param status: expected status of the last dispatched message
        :param progress: expected progress of the last dispatched message, None to skip the check
        """
        self.assertEqual(len(observer.messages), expected_count)
        last_message = observer.messages[expected_count - 1]
        self.assertEqual(last_message.message, message)
        self.assertEqual(last_message.status, status)
        if progress is not None:
            self.assertEqual(last_message.progress, progress)

    def test_notify_message_with_format(self):
        """Test the notify_message_with_format method with various formats."""

        # Use DEBUG level to allow all message types through
        dispatcher = MessageDispatcher(0, 0, log_level=MessageLevel.DEBUG)

        observer = BasicMessageObserver()
        dispatcher.attach(observer)

        # Test INFO format
        dispatcher.notify_message_with_format("[INFO] This is an info message")
        self._assert_dispatched_message(observer, 1, "This is an info message", "INFO")

        # Test WARNING format
        dispatcher.notify_message_with_format("[WARNING] This is a warning")
        self._assert_dispatched_message(observer, 2, "This is a warning", "WARNING")

        # Test ERROR format
        dispatcher.notify_message_with_format("[ERROR] This is an error")
        self._assert_dispatched_message(observer, 3, "This is an error", "ERROR")

        # Test SUCCESS format
        dispatcher.notify_message_with_format("[SUCCESS] Operation successful")
        self._assert_dispatched_message(observer, 4, "Operation successful", "SUCCESS")

        # Test DEBUG format
        dispatcher.notify_message_with_format("[DEBUG] Debug information")
        self._assert_dispatched_message(observer, 5, "Debug information", "DEBUG")

        # Test PROGRESS format with integer value
        dispatcher.notify_message_with_format("[PROGRESS:50] Half way done")
        self._assert_dispatched_message(observer, 6, "Half way done", "PROGRESS", 50.0)

        # Test PROGRESS format with float value
        dispatcher.notify_message_with_format("[PROGRESS:75.5] Almost complete")
        self._assert_dispatched_message(observer, 7, "Almost complete", "PROGRESS", 75.5)

        # Test PROGRESS format with no message
        dispatcher.notify_message_with_format("[PROGRESS:100]")
        self._assert_dispatched_message(observer, 8, "", "PROGRESS", 100.0)

        # Test message without format prefix (defaults to INFO)
        dispatcher.notify_message_with_format("Regular message without prefix")
        self._assert_dispatched_message(observer, 9, "Regular message without prefix", "INFO")

        # Test invalid PROGRESS value (> 100) - should be treated as INFO
        dispatcher.notify_message_with_format("[PROGRESS:150] Invalid progress")
        self._assert_dispatched_message(observer, 10, "[PROGRESS:150] Invalid progress", "INFO")

        # Test invalid PROGRESS value (< 0) - should be treated as INFO
        dispatcher.notify_message_with_format("[PROGRESS:-10] Negative progress")
        self._assert_dispatched_message(observer, 11, "[PROGRESS:-10] Negative progress", "INFO")

        # Test invalid PROGRESS format (non-numeric) - should be treated as INFO
        dispatcher.notify_message_with_format("[PROGRESS:abc] Invalid number")
        self._assert_dispatched_message(observer, 12, "[PROGRESS:abc] Invalid number", "INFO")

        # Test unknown prefix - should be treated as INFO with original message
        dispatcher.notify_message_with_format("[UNKNOWN] Unknown message type")
        self._assert_dispatched_message(observer, 13, "[UNKNOWN] Unknown message type", "INFO")

        # Test message with no closing bracket - should be treated as INFO
        dispatcher.notify_message_with_format("[INFO No closing bracket")
        self._assert_dispatched_message(observer, 14, "[INFO No closing bracket", "INFO")
