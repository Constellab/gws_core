

from time import sleep

from gws_core import BaseTestCase
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_level import MessageLevel
from gws_core.core.classes.observer.message_observer import \
    BasicMessageObserver
from gws_core.progress_bar.progress_bar import ProgressBar


# test_dispatcher
class TestDispatcher(BaseTestCase):

    def test_dispatcher(self):
        dispatcher = MessageDispatcher(0.05, 0.25)

        observer = BasicMessageObserver()
        dispatcher.attach(observer)

        dispatcher.notify_info_message('message 1')
        sleep(0.30)
        self.assertEqual(len(observer.messages), 1)
        self.assertEqual(observer.messages[0].message, 'message 1')
        self.assertEqual(observer.messages[0].status, 'INFO')

        # check that multiple messages are merged
        dispatcher.notify_info_message('message 2')
        dispatcher.notify_info_message('message 3')
        sleep(0.30)
        self.assertEqual(len(observer.messages), 2)
        self.assertEqual(observer.messages[1].message, 'message 2\nmessage 3')

        # check that slower messages are not merge but dispatched 1 time
        dispatcher.notify_info_message('message 4')
        self.assertEqual(len(observer.messages), 2)
        sleep(0.10)
        dispatcher.notify_info_message('message 5')
        sleep(0.30)
        self.assertEqual(len(observer.messages), 4)
        self.assertEqual(observer.messages[2].message, 'message 4')
        self.assertEqual(observer.messages[3].message, 'message 5')

        # test direct dispatch
        dispatcher.notify_info_message('message 6')
        dispatcher.force_dispatch_waiting_messages()
        self.assertEqual(len(observer.messages), 5)
        self.assertEqual(observer.messages[4].message, 'message 6')

    def test_dispatcher_with_progress_bar(self):
        dispatcher = MessageDispatcher(0.05, 0.25)

        try:

            progress_bar = ProgressBar()
            dispatcher.attach_progress_bar(progress_bar)

            dispatcher.notify_info_message('message 1')
            sleep(0.30)

            self.assertEqual(len(progress_bar.get_messages()), 1)
            self.assertEqual(progress_bar.get_messages()[0].text, 'message 1')
        except Exception as err:
            dispatcher.force_dispatch_waiting_messages()
            raise err

    def test_level(self):
        dispatcher = MessageDispatcher(0, 0)

        observer = BasicMessageObserver()
        dispatcher.attach(observer)

        dispatcher.notify_debug_message('message 1')
        self.assertEqual(len(observer.messages), 0)

        dispatcher.notify_info_message('message 1')
        self.assertEqual(len(observer.messages), 1)

    def test_notify_message_with_format(self):
        """Test the notify_message_with_format method with various formats."""

        # Use DEBUG level to allow all message types through
        dispatcher = MessageDispatcher(0, 0, log_level=MessageLevel.DEBUG)

        observer = BasicMessageObserver()
        dispatcher.attach(observer)

        # Test INFO format
        dispatcher.notify_message_with_format('[INFO] This is an info message')
        self.assertEqual(len(observer.messages), 1)
        self.assertEqual(observer.messages[0].message, 'This is an info message')
        self.assertEqual(observer.messages[0].status, 'INFO')

        # Test WARNING format
        dispatcher.notify_message_with_format('[WARNING] This is a warning')
        self.assertEqual(len(observer.messages), 2)
        self.assertEqual(observer.messages[1].message, 'This is a warning')
        self.assertEqual(observer.messages[1].status, 'WARNING')

        # Test ERROR format
        dispatcher.notify_message_with_format('[ERROR] This is an error')
        self.assertEqual(len(observer.messages), 3)
        self.assertEqual(observer.messages[2].message, 'This is an error')
        self.assertEqual(observer.messages[2].status, 'ERROR')

        # Test SUCCESS format
        dispatcher.notify_message_with_format('[SUCCESS] Operation successful')
        self.assertEqual(len(observer.messages), 4)
        self.assertEqual(observer.messages[3].message, 'Operation successful')
        self.assertEqual(observer.messages[3].status, 'SUCCESS')

        # Test DEBUG format
        dispatcher.notify_message_with_format('[DEBUG] Debug information')
        self.assertEqual(len(observer.messages), 5)
        self.assertEqual(observer.messages[4].message, 'Debug information')
        self.assertEqual(observer.messages[4].status, 'DEBUG')

        # Test PROGRESS format with integer value
        dispatcher.notify_message_with_format('[PROGRESS:50] Half way done')
        self.assertEqual(len(observer.messages), 6)
        self.assertEqual(observer.messages[5].message, 'Half way done')
        self.assertEqual(observer.messages[5].status, 'PROGRESS')
        self.assertEqual(observer.messages[5].progress, 50.0)

        # Test PROGRESS format with float value
        dispatcher.notify_message_with_format('[PROGRESS:75.5] Almost complete')
        self.assertEqual(len(observer.messages), 7)
        self.assertEqual(observer.messages[6].message, 'Almost complete')
        self.assertEqual(observer.messages[6].status, 'PROGRESS')
        self.assertEqual(observer.messages[6].progress, 75.5)

        # Test PROGRESS format with no message
        dispatcher.notify_message_with_format('[PROGRESS:100]')
        self.assertEqual(len(observer.messages), 8)
        self.assertEqual(observer.messages[7].message, '')
        self.assertEqual(observer.messages[7].status, 'PROGRESS')
        self.assertEqual(observer.messages[7].progress, 100.0)

        # Test message without format prefix (defaults to INFO)
        dispatcher.notify_message_with_format('Regular message without prefix')
        self.assertEqual(len(observer.messages), 9)
        self.assertEqual(observer.messages[8].message, 'Regular message without prefix')
        self.assertEqual(observer.messages[8].status, 'INFO')

        # Test invalid PROGRESS value (> 100) - should be treated as INFO
        dispatcher.notify_message_with_format('[PROGRESS:150] Invalid progress')
        self.assertEqual(len(observer.messages), 10)
        self.assertEqual(observer.messages[9].message, '[PROGRESS:150] Invalid progress')
        self.assertEqual(observer.messages[9].status, 'INFO')

        # Test invalid PROGRESS value (< 0) - should be treated as INFO
        dispatcher.notify_message_with_format('[PROGRESS:-10] Negative progress')
        self.assertEqual(len(observer.messages), 11)
        self.assertEqual(observer.messages[10].message, '[PROGRESS:-10] Negative progress')
        self.assertEqual(observer.messages[10].status, 'INFO')

        # Test invalid PROGRESS format (non-numeric) - should be treated as INFO
        dispatcher.notify_message_with_format('[PROGRESS:abc] Invalid number')
        self.assertEqual(len(observer.messages), 12)
        self.assertEqual(observer.messages[11].message, '[PROGRESS:abc] Invalid number')
        self.assertEqual(observer.messages[11].status, 'INFO')

        # Test unknown prefix - should be treated as INFO with original message
        dispatcher.notify_message_with_format('[UNKNOWN] Unknown message type')
        self.assertEqual(len(observer.messages), 13)
        self.assertEqual(observer.messages[12].message, '[UNKNOWN] Unknown message type')
        self.assertEqual(observer.messages[12].status, 'INFO')

        # Test message with no closing bracket - should be treated as INFO
        dispatcher.notify_message_with_format('[INFO No closing bracket')
        self.assertEqual(len(observer.messages), 14)
        self.assertEqual(observer.messages[13].message, '[INFO No closing bracket')
        self.assertEqual(observer.messages[13].status, 'INFO')
