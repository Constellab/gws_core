# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import os
from datetime import datetime

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper

from .log import LogCompleteInfo, LogInfo, LogsBetweenDatesResponse, LogsStatus


class LogService:

    @classmethod
    def get_logs_status(cls) -> LogsStatus:

        log_folder = Settings.get_instance().get_log_dir()
        log_status: LogsStatus = {"log_folder": log_folder, "log_files": []}

        for node_name in os.listdir(log_folder):
            log_info = cls.get_log_info(node_name)

            if log_info is not None:
                log_status["log_files"].append(log_info)

        # sort logs_files by name
        log_status["log_files"].sort(key=lambda x: x["name"])

        return log_status

    @classmethod
    def get_log_complete_info(cls, node_name: str) -> LogCompleteInfo:
        log_info = cls.get_log_info(node_name)

        if log_info is None:
            raise BadRequestException(f"File {node_name} is not a log file")

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
                               from_experiment: bool = None) -> LogsBetweenDatesResponse:

        if not DateHelper.are_same_day(from_date, to_date):
            raise BadRequestException("The dates must be on the same day")

        log_file_name = Logger.date_to_file_name(from_date)

        log_complete_info = cls.get_log_complete_info(log_file_name)
        log_lines = log_complete_info.get_log_lines_by_time(from_date, to_date, from_experiment)
        return LogsBetweenDatesResponse(logs=log_lines, from_date=from_date, to_date=to_date,
                                        from_experiment=from_experiment)

    @classmethod
    def get_log_file_path(cls, node_name: str) -> str:
        log_info = cls.get_log_info(node_name)

        if log_info is None:
            raise BadRequestException(f"File {node_name} is not a log file")

        return os.path.join(Settings.get_instance().get_log_dir(), node_name)
