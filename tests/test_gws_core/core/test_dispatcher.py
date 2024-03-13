

from time import sleep

from gws_core import BaseTestCase
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
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
