# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from time import sleep
from unittest import IsolatedAsyncioTestCase

from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.lab.log.log import LogCompleteInfo
from gws_core.lab.log.log_service import LogService, LogsStatus


# test_log_service
class TestLogService(IsolatedAsyncioTestCase):

    def test_get_logs_status(self):
        Logger.info('test_get_logs_status')

        logs_status: LogsStatus = LogService.get_logs_status()

        self.assertEqual(logs_status['log_folder'], Settings.get_instance().get_log_dir())
        self.assertEqual(len(logs_status['log_files']), 1)

        log_info = logs_status['log_files'][0]
        self.assertEqual(log_info['name'], 'log')
        self.assertTrue(log_info['file_size'] > 0)

        # get complete log
        log_complete_info: LogCompleteInfo = LogService.get_log_complete_info(log_info['name'])
        self.assertIsNotNone(log_complete_info.log_info)

        content = log_complete_info.content
        self.assertTrue(len(content) > 0)
        # check that the log contains the message of the test
        self.assertTrue('test_get_logs_status\n' in content)
        self.assertEqual(log_complete_info.get_log_file_date(), DateHelper.now_utc().date())

    def test_complete_log_info(self):

        log_content = """INFO - 2022-12-01 09:24:46.905469 -  START APPLICATION : gws_core version 0.4.0, log level: INFO
INFO - 2022-12-01 09:26:46.906581 - first - log
INFO - 2022-12-01 09:30:46.947581 - [EXPERIMENT] - second_log
"""

        log_complete_info: LogCompleteInfo = LogCompleteInfo(
            {'name': 'log.2022-12-01', 'file_size': 0}, log_content)

        self.assertEqual(log_complete_info.get_log_file_date(),
                         DateHelper.from_str('01-12-2022', '%d-%m-%Y').date())

        from_date = DateHelper.from_iso_str('2022-12-01T09:25:00+00:00')
        to_date = DateHelper.from_iso_str('2022-12-01T09:32:00+00:00')

        log_lines = log_complete_info.get_log_lines_by_time(from_date, to_date)
        self.assertEqual(len(log_lines), 2)
        self.assertEqual(log_lines[0].content, 'first - log')

        first_log_date = DateHelper.from_iso_str('2022-12-01T09:26:46.906581+00:00')
        self.assertEqual(log_lines[0].date_time, first_log_date)
        self.assertEqual(log_lines[0].level, 'INFO')
        self.assertFalse(log_lines[0].is_from_experiment)

        self.assertEqual(log_lines[1].content, 'second_log')
        self.assertTrue(log_lines[1].is_from_experiment)

        log_lines = log_complete_info.get_log_lines_by_time(from_date, to_date, from_experiment=True)
        self.assertEqual(len(log_lines), 1)

    def setUp(self) -> None:
        FileHelper.delete_dir_content(Settings.get_instance().get_log_dir())
        Logger._logger = None
        Logger(level='INFO', _is_experiment_process=False)

    def tearDown(self) -> None:
        FileHelper.delete_dir_content(Settings.get_instance().get_log_dir())
