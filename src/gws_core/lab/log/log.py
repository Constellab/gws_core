# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from datetime import date, datetime, timedelta
from json import loads
from typing import List

from typing_extensions import TypedDict

from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import LogFileLine, Logger, MessageType


class LogInfo(TypedDict):

    name: str
    file_size: int


class LogsStatus(TypedDict):

    log_folder: str
    log_files: List[LogInfo]


class LogLine():
    """Object that represent a line of a log file like
    INFO - 2022-12-08 09:50:05.558872 - START APPLICATION : gws_core version 0.4.0

    or
    INFO - 2022-12-08 09:50:05.558872 - [EXPERIMENT] - START APPLICATION : gws_core version 0.4.0

    :raises ValueError: _description_
    :return: _description_
    :rtype: _type_
    """

    full_line: str

    level: MessageType
    date_time: datetime
    is_from_experiment: bool
    experiment_id: str
    message: str

    OLD_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

    def __init__(self, line_str: str) -> None:
        if line_str is None or len(line_str) == 0:
            raise ValueError("line_str is empty")
        self.full_line = line_str

        self.level = None
        self.date_time = None
        self.message = None
        self.is_from_experiment = False
        self.experiment_id = None

        if line_str[0] == '{':
            self._init_new(line_str)
        else:
            self._init_old(line_str)

    def _init_new(self, line_str: str) -> None:
        """
        Read the line as json and extract the level, date, content and if it is from an experiment
        """
        try:
            line_json: LogFileLine = loads(line_str)
            self.level = line_json.get('level')
            self.init_new_date(line_json.get('timestamp'))
            self.message = line_json.get('message')
            self.is_from_experiment = line_json.get('experiment_id') is not None
            self.experiment_id = line_json.get('experiment_id')
        except ValueError:
            pass

    def _init_old(self, line_str: str) -> None:
        """Read the line and extract the level, date, content and if it is from an experiment
        Line example : INFO - 2023-07-12 14:10:09,676 - Logger configured with log level: INFO
        The log system was changed on v0.5.7

        :param line_str: _description_
        :type line_str: str
        """
        separator = Logger.SEPARATOR
        logs_parts = line_str.split(separator)

        if len(logs_parts) >= 3:
            self.level = logs_parts[0]

            self.init_old_date(logs_parts[1])

            # if the log also contains the text ' - [EXPERIMENT] - '
            # it is from an experiment
            if len(logs_parts) >= 4 and logs_parts[2] == Logger.SUB_PROCESS_TEXT:
                # use a join because the log can contains ' - '
                self.message = separator.join(logs_parts[3:])
                self.is_from_experiment = True
            else:
                # use a join because the log can contains ' - '
                self.message = separator.join(logs_parts[2:])
                self.is_from_experiment = False

    def init_old_date(self, date_str: str) -> None:
        try:
            date_time = DateHelper.from_str(date_str, LogLine.OLD_DATE_FORMAT)
            self.date_time = DateHelper.convert_datetime_to_utc(date_time)
        except ValueError:
            pass

    def init_new_date(self, date_str: str) -> None:
        try:
            date_time = DateHelper.from_iso_str(date_str)
            self.date_time = DateHelper.convert_datetime_to_utc(date_time)
        except ValueError:
            pass

    def is_valid(self) -> bool:
        return self.level is not None and \
            self.date_time is not None and \
            self.message is not None

    def get_datetime_without_microseconds(self) -> datetime:
        return self.date_time.replace(microsecond=self.date_time.microsecond // 1000 * 1000)

    def to_json(self) -> dict:
        return {"level": self.level, "date_time": self.date_time,
                "message": self.message, "experiment_id": self.experiment_id}

    def to_str(self) -> str:
        return f"{self.level} - {self.date_time} - {self.message}"


class LogCompleteInfo():

    log_info: LogInfo
    content: str

    def __init__(self, log_info: LogInfo, content: str) -> None:
        self.log_info = log_info
        self.content = content

    def get_log_file_date(self) -> date:
        name = self.log_info["name"]
        return Logger.file_name_to_date(name).date()

    def get_log_lines_by_time(self, start_time: datetime, end_time: datetime,
                              from_experiment_id: str = None,
                              nb_of_lines: int = None) -> List[LogLine]:
        """Filter the log lines by time and if it is from an experiment

        :param start_time: start time of the filter
        :type start_time: datetime
        :param end_time: end time of the filter
        :type end_time: datetime
        :param from_experiment: if provided filter only log with the bool, defaults to None
        :type from_experiment: bool, optional
        :return: _description_
        :rtype: List[LogLine]
        """
        log_lines: List[LogLine] = []
        stop_date: datetime = None

        for line in self.content.splitlines():
            if len(line) == 0:
                continue
            log_line = LogLine(line)

            if not log_line.is_valid():
                continue

            # if the page date is provided, stop the loop when the nb is reached
            # if the next line is the exact same date ignoring the microseconds add it to the list
            if stop_date is not None and log_line.get_datetime_without_microseconds() != stop_date:
                break

            # if the experiment id is provided, filter the log lines
            # skip lines that are not from the experiment
            # also skip lines that are from another experiment
            # if the experiment id is not provided, don't skip this is old format
            if from_experiment_id is not None and (
                    not log_line.is_from_experiment
                    or (log_line.experiment_id is not None and log_line.experiment_id != from_experiment_id)):
                continue

            if start_time <= log_line.date_time <= end_time:
                log_lines.append(log_line)

            if nb_of_lines is not None and len(log_lines) >= nb_of_lines:
                stop_date = log_line.get_datetime_without_microseconds()

        return log_lines

    def to_json(self) -> dict:
        return {"log_info": self.log_info, "content": self.content}


class LogsBetweenDatesDTO():

    logs: List[LogLine]
    from_date: datetime
    to_date: datetime
    from_experiment_id: str
    is_last_page: bool

    def __init__(self, logs: List[LogLine], from_date: datetime, to_date: datetime,
                 from_experiment_id: str, is_last_page: bool) -> None:
        self.logs = logs
        self.from_date = from_date
        self.to_date = to_date
        self.from_experiment_id = from_experiment_id
        self.is_last_page = is_last_page

    def to_json(self) -> dict:
        return {
            "logs": [log.to_json() for log in self.logs],
            "from_date": self.from_date,
            "to_date": self.to_date,
            "from_experiment_id": self.from_experiment_id,
            "is_last_page": self.is_last_page,
            "next_page_date": self.get_next_page_date()
        }

    def get_next_page_date(self) -> datetime:
        """return the start date for the next page
        Add 1 millisecond to the last log date to avoid duplicate logs

        :return: _description_
        :rtype: datetime
        """
        return self.logs[-1].date_time + timedelta(milliseconds=1) if len(self.logs) > 0 else None

    def to_str(self) -> str:
        return "\n".join([log.to_str() for log in self.logs])
