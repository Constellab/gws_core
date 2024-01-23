# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
from unittest import TestCase

from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.lab.log.log import LogCompleteInfo, LogsBetweenDates
from gws_core.lab.log.log_dto import LogsStatusDTO
from gws_core.lab.log.log_service import LogService


# test_log_service
class TestLogService(TestCase):

    log_1_date = DateHelper.from_str('01-12-2022', '%d-%m-%Y')
    log_2_date = DateHelper.from_str('02-12-2022', '%d-%m-%Y')

    def test_get_logs_status(self):
        Logger.info('test_get_logs_status')

        logs_status: LogsStatusDTO = LogService.get_logs_status()

        self.assertEqual(logs_status.log_folder, Settings.get_instance().get_log_dir())
        self.assertEqual(len(logs_status.log_files), 3)

        log_info = logs_status.log_files[0]
        self.assertEqual(log_info.name, 'log')
        self.assertTrue(log_info.file_size > 0)

        # get complete log
        log_complete_info: LogCompleteInfo = LogService.get_log_complete_info(log_info.name)
        self.assertIsNotNone(log_complete_info.log_info)

        content = log_complete_info.content
        self.assertTrue(len(content) > 0)
        # check that the log contains the message of the test
        self.assertTrue('test_get_logs_status' in content)
        self.assertEqual(log_complete_info.get_log_file_date(), DateHelper.now_utc().date())

    def test_get_logs_between_same_dates(self):

        from_date = DateHelper.from_iso_str('2022-12-01:00:00+00:00')
        to_date = DateHelper.from_iso_str('2022-12-01T23:32:00+00:00')

        result: LogsBetweenDates = LogService.get_logs_between_dates(from_date, to_date)
        self.assertEqual(len(result.logs), 3)

    def test_get_between_dates_and_pagination(self):

        # get logs on multiple dates
        from_date = DateHelper.from_iso_str('2022-12-01:00:00+00:00')
        # skip the last message of the log file 2
        to_date = DateHelper.from_iso_str('2022-12-02T23:32:00+00:00')

        result: LogsBetweenDates = LogService.get_logs_between_dates(from_date, to_date)
        self.assertEqual(len(result.logs), 6)

        # get only log from experiment
        result: LogsBetweenDates = LogService.get_logs_between_dates(from_date, to_date,
                                                                     from_experiment_id="1234567890")
        self.assertEqual(len(result.logs), 2)

        # get logs paginated and skip the first log and the last log
        from_date = DateHelper.from_iso_str('2022-12-01:09:00+00:00')
        to_date = DateHelper.from_iso_str('2022-12-02T09:32:00+00:00')

        result: LogsBetweenDates = LogService.get_logs_between_dates(from_date, to_date, nb_of_lines=3)
        self.assertEqual(len(result.logs), 3)
        self.assertEqual(result.logs[0].message, 'first - log day 1')
        self.assertEqual(result.logs[1].message, 'second - log day 1')
        self.assertEqual(result.logs[2].message, 'Day 2')

        # get next page
        result: LogsBetweenDates = LogService.get_logs_between_dates(
            result.get_next_page_date(), to_date, nb_of_lines=3)
        self.assertEqual(len(result.logs), 1)
        self.assertEqual(result.logs[0].message, 'first - log day 2')

    def setUp(self) -> None:
        log_dir = Settings.get_instance().get_log_dir()
        FileHelper.delete_dir_content(log_dir)
        Logger.clear_logger()
        Logger(Settings.build_log_dir(True), level='INFO')

        log_content_1 = """{"level": "INFO", "timestamp": "2022-12-01T08:24:46.905469+00:00", "message": "Day 1"}
INFO - 2022-12-01 09:26:46.906581 - first - log day 1
INFO - 2022-12-01 09:30:46.947581 - [EXPERIMENT] - second - log day 1
"""

        log_content_2 = """{"level": "INFO", "timestamp": "2022-12-02 09:24:46.905469", "message": "Day 2"}
INFO - 2022-12-02 09:26:46.906581 - first - log day 2
{"level": "INFO", "timestamp": "2022-12-02T19:30:46.947581+00:00", "message": "second - log day 2", "experiment_id": "1234567890"}
"""
        # create logs files

        # write log file 1
        log_file_path = os.path.join(log_dir, Logger.date_to_file_name(self.log_1_date))
        with open(log_file_path, "w", encoding='UTF-8') as f:
            f.write(log_content_1)

        # write log file 2
        log_file_path = os.path.join(log_dir, Logger.date_to_file_name(self.log_2_date))
        with open(log_file_path, "w", encoding='UTF-8') as f:
            f.write(log_content_2)

    def tearDown(self) -> None:
        FileHelper.delete_dir_content(Settings.get_instance().get_log_dir())
