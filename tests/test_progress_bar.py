

from time import sleep

from gws_core import ProgressBar, ProgressBarMessageType
from gws_core.test.base_test_case import BaseTestCase


class TestProgressBar(BaseTestCase):

    def test_progress_bar(self):
        progress_bar: ProgressBar = ProgressBar()

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

        sleep(ProgressBar._min_allowed_delta_time)
        # Test progress message
        progress_bar.update_progress(25, 'New progress')
        progress_message = progress_bar.messages[1]
        self.assertEqual(progress_message['text'], '25.0%: New progress')
        self.assertTrue(progress_bar.is_running)

        progress_bar.stop_success('Finish')
        self.assertFalse(progress_bar.is_running)
        self.assertTrue(progress_bar.is_finished)

        # test that the progress bar was correcly save
        progress_bar_db: ProgressBar = ProgressBar.get_by_uri_and_check(progress_bar.uri)
        self.assertEqual(len(progress_bar_db.messages), 3)
        self.assertTrue(progress_bar_db.is_finished)
