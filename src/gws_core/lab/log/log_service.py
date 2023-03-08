# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import os
from datetime import datetime
from typing import List

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper

from .log import (LogCompleteInfo, LogInfo, LogLine, LogsBetweenDatesDTO,
                  LogsStatus)


class LogService:

    @classmethod
    def get_logs_status(cls) -> LogsStatus:

        log_folder = Settings.get_instance().get_log_dir()
        log_status: LogsStatus = {"log_folder": log_folder, "log_files": []}

        for node_name in os.listdir(log_folder):
            log_info = cls.get_log_info(node_name)

            if log_info is not None:
                log_status["log_files"].append(log_info)

        # sort logs_files by name in reverse but keep the last log file named 'log' at the top
        log_status["log_files"].sort(key=lambda log: log["name"], reverse=True)
        log_status["log_files"].sort(key=lambda log: log["name"] == "log", reverse=True)

        return log_status

    @classmethod
    def get_log_complete_info(cls, node_name: str) -> LogCompleteInfo:
        log_info = cls.get_log_info(node_name)

        if log_info is None:
            raise BadRequestException(f"File '{node_name}' is not a log file")

        log_folder = Settings.get_instance().get_log_dir()
        log_file_path = os.path.join(log_folder, node_name)

        with open(log_file_path, "r", encoding='UTF-8') as f:
            content = f.read()

        return LogCompleteInfo(log_info, content)

    @classmethod
    def get_log_info(cls, node_name: str) -> LogInfo:
        log_folder = Settings.get_instance().get_log_dir()

        if not node_name.startswith('log'):
            return None

        log_file_path = os.path.join(log_folder, node_name)
        if not FileHelper.is_file(log_file_path):
            return None

        return {
            "name": node_name,
            "file_size": FileHelper.get_size(log_file_path),
        }

    @classmethod
    def get_logs_between_dates(cls, from_date: datetime, to_date: datetime,
                               from_experiment: bool = None) -> LogsBetweenDatesDTO:

        log_lines: List[LogLine] = []

        # retrieve logs for each day
        for date in DateHelper.date_range(from_date, to_date, include_end_date=True):
            one_day_from: datetime = None
            one_day_to: datetime = None
            # if the from_date is the same day as the date, we use the from_date
            # otherwise with use the date at 00:00:00
            if DateHelper.are_same_day(from_date, date):
                one_day_from = DateHelper.convert_datetime_to_utc(from_date)
            else:
                one_day_from = DateHelper.convert_datetime_to_utc(
                    datetime(year=date.year, month=date.month, day=date.day))

            # if the to_date is the same day as the date, we use the to_date
            # otherwise with use the date at 23:59:59
            if DateHelper.are_same_day(to_date, date):
                one_day_to = DateHelper.convert_datetime_to_utc(to_date)
            else:
                one_day_to = DateHelper.convert_datetime_to_utc(
                    datetime(
                        year=date.year, month=date.month, day=date.day,
                        hour=23, minute=59, second=59))

            try:
                log_lines.extend(cls.get_logs_between_dates_same_day(one_day_from, one_day_to, from_experiment))
            # skip error : file is not log file
            except BadRequestException:
                continue

        return LogsBetweenDatesDTO(logs=log_lines, from_date=from_date, to_date=to_date,
                                   from_experiment=from_experiment)

    @classmethod
    def get_logs_between_dates_same_day(cls, from_date: datetime, to_date: datetime,
                                        from_experiment: bool = None) -> List[LogLine]:

        if not DateHelper.are_same_day(from_date, to_date):
            raise BadRequestException("The dates must be on the same day")

        log_file_name = Logger.date_to_file_name(from_date)

        log_complete_info = cls.get_log_complete_info(log_file_name)
        return log_complete_info.get_log_lines_by_time(from_date, to_date, from_experiment)

    @classmethod
    def get_log_file_path(cls, node_name: str) -> str:
        log_info = cls.get_log_info(node_name)

        if log_info is None:
            raise BadRequestException(f"File {node_name} is not a log file")

        return os.path.join(Settings.get_instance().get_log_dir(), node_name)
