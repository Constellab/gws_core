# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from time import sleep

from gws_core import ProgressBar, ProgressBarMessageType
from gws_core.test.base_test_case import BaseTestCase


# test_progress_bar
class TestProgressBar(BaseTestCase):

    def test_progress_bar(self):
        progress_bar: ProgressBar = ProgressBar()
        # for test remove delta time
        progress_bar._MIN_ALLOWED_DELTA_TIME = 0

        self.assertIsNotNone(progress_bar.data)

        progress_bar.save()
        self.assertIsNotNone(progress_bar.id)

        self.assertFalse(progress_bar.is_running)
        self.assertFalse(progress_bar.is_finished)
        progress_bar.start()
        progress_bar.add_success_message('Hello')

        self.assertEqual(len(progress_bar.messages), 1)
        messages = progress_bar.messages[0]
        self.assertEqual(messages['type'], ProgressBarMessageType.SUCCESS)
        self.assertEqual(messages['text'], 'Hello')
        self.assertIsNotNone(messages['datetime'])

        # Test progress message
        progress_bar.update_progress(25, 'New progress')
        progress_message = progress_bar.messages[1]
        self.assertEqual(progress_message['text'], '25.0%: New progress')
        self.assertTrue(progress_bar.is_running)

        progress_bar.stop_success('Finish')
        self.assertFalse(progress_bar.is_running)
        self.assertTrue(progress_bar.is_finished)

        # test that the progress bar was correcly save
        progress_bar_db: ProgressBar = ProgressBar.get_by_id_and_check(progress_bar.id)
        self.assertEqual(len(progress_bar_db.messages), 3)
        self.assertTrue(progress_bar_db.is_finished)

    def test_mulitple_messages(self):
        ProgressBar._MIN_ALLOWED_DELTA_TIME = 1.0
        progress_bar: ProgressBar = ProgressBar()
        progress_bar.add_success_message('Hello')

        # test that the first message is directly saved
        progress_bar: ProgressBar = ProgressBar.get_by_id_and_check(progress_bar.id)
        self.assertEqual(len(progress_bar.messages), 1)

        # 2 message added consecutively should not save the progress bar directly
        progress_bar.add_error_message('Error')
        progress_bar.add_message('Message')
        # verify the timer was created
        self.assertIsNotNone(progress_bar._save_timer)
        progress_bar: ProgressBar = ProgressBar.get_by_id_and_check(progress_bar.id)
        self.assertNotEqual(len(progress_bar.messages), 3)

        # wait for the progress bar to save the messages
        sleep(progress_bar._MIN_ALLOWED_DELTA_TIME + 0.3)
        progress_bar: ProgressBar = ProgressBar.get_by_id_and_check(progress_bar.id)
        self.assertEqual(len(progress_bar.messages), 3)

        # force save
        progress_bar.add_error_message('Error')
        progress_bar.add_message('Message')
        progress_bar.save()
        self.assertIsNone(progress_bar._save_timer)
        progress_bar: ProgressBar = ProgressBar.get_by_id_and_check(progress_bar.id)
        self.assertEqual(len(progress_bar.messages), 5)

        ProgressBar._MIN_ALLOWED_DELTA_TIME = 0
