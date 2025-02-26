

from gws_core import MessageLevel, ProgressBar
from gws_core.core.utils.date_helper import DateHelper
from gws_core.test.base_test_case import BaseTestCase


# test_progress_bar
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

        self.assertEqual(len(progress_bar.get_messages()), 1)
        messages = progress_bar.get_messages()[0]
        self.assertEqual(messages.type, MessageLevel.SUCCESS)
        self.assertEqual(messages.text, 'Hello')
        self.assertIsNotNone(messages.datetime)

        # Test progress message
        progress_bar.update_progress(25, 'New progress')
        progress_message = progress_bar.get_messages()[1]
        self.assertEqual(progress_message.text, 'New progress')
        self.assertEqual(progress_message.progress, 25.0)
        self.assertTrue(progress_bar.is_running)

        progress_bar.stop_success('Finish', 1)
        self.assertFalse(progress_bar.is_running)
        self.assertTrue(progress_bar.is_finished)

        # test that the progress bar was correcly save
        progress_bar_db: ProgressBar = ProgressBar.get_by_id_and_check(
            progress_bar.id)
        self.assertEqual(len(progress_bar_db.get_messages()), 3)
        self.assertTrue(progress_bar_db.is_finished)

    def test_get_paginated(self):
        progress_bar: ProgressBar = ProgressBar()
        progress_bar.data['messages'] = [
            {'type': 'SUCCESS', 'text': 'Hello1',
                'datetime': '2021-01-01T00:00:00'},
            {'type': 'SUCCESS', 'text': 'Hello2',
                'datetime': '2021-01-02T00:00:01'},
            {'type': 'SUCCESS', 'text': 'Hello3',
                'datetime': '2021-01-03T00:00:01'},
            {'type': 'SUCCESS', 'text': 'Hello4',
                'datetime': '2021-01-04T00:00:01'},
        ]

        messages = progress_bar.get_messages_paginated(
            nb_of_messages=2, before_date=None)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].text, 'Hello4')
        self.assertEqual(messages[1].text, 'Hello3')

        from_date = DateHelper.from_iso_str('2021-01-03T00:00:00')
        messages = progress_bar.get_messages_paginated(
            nb_of_messages=2, before_date=from_date)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].text, 'Hello2')
        self.assertEqual(messages[1].text, 'Hello1')
