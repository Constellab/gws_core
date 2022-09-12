# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from time import sleep

from gws_core import BaseTestCase
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import \
    BasicMessageObserver
from gws_core.progress_bar.progress_bar import ProgressBar


# test_dispatcher
class TestDispatcher(BaseTestCase):

    async def test_dispatcher(self):
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

    async def test_dispatcher_with_progress_bar(self):
        dispatcher = MessageDispatcher(0.05, 0.25)

        progress_bar = ProgressBar()
        dispatcher.attach_progress_bar(progress_bar)

        dispatcher.notify_info_message('message 1')
        sleep(0.30)

        self.assertEqual(len(progress_bar.messages), 1)
        self.assertEqual(progress_bar.messages[0]['text'], 'message 1')
