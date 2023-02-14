# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from datetime import date, datetime
from typing import List

from typing_extensions import TypedDict

from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import Logger, MessageType


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
    content: str

    def __init__(self, line_str: str) -> None:
        if line_str is None or len(line_str) == 0:
            raise ValueError("line_str is empty")
        self.full_line = line_str

        separator = Logger.SEPARATOR
        logs_parts = line_str.split(separator)

        if len(logs_parts) >= 3:
            self.level = logs_parts[0]

            try:
                date_time = DateHelper.from_str(logs_parts[1], Logger.DATE_FORMAT)
                self.date_time = DateHelper.convert_datetime_to_utc(date_time)
            except ValueError:
                self.date_time = None

            # if the log also contains the text ' - [EXPERIMENT] - '
            # it is from an experiment
            if len(logs_parts) >= 4 and logs_parts[2] == Logger.SUB_PROCESS_TEXT:
                # use a join because the log can contains ' - '
                self.content = separator.join(logs_parts[3:])
                self.is_from_experiment = True
            else:
                # use a join because the log can contains ' - '
                self.content = separator.join(logs_parts[2:])
                self.is_from_experiment = False

        else:
            self.level = None
            self.date_time = None
            self.content = None

    def is_valid(self) -> bool:
        return self.level is not None and \
            self.date_time is not None and \
            self.content is not None

    def to_json(self) -> dict:
        return {"level": self.level, "date_time": self.date_time,
                "content": self.content, "is_from_experiment": self.is_from_experiment}


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
                              from_experiment: bool = None) -> List[LogLine]:
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
        for line in self.content.splitlines():
            if len(line) == 0:
                continue
            log_line = LogLine(line)

            if not log_line.is_valid():
                continue

            if from_experiment is not None and log_line.is_from_experiment != from_experiment:
                continue

            if start_time <= log_line.date_time <= end_time:
                log_lines.append(log_line)
        return log_lines

    def to_json(self) -> dict:
        return {"log_info": self.log_info, "content": self.content}


class LogsBetweenDatesDTO():

    logs: List[LogLine]
    from_date: datetime
    to_date: datetime
    from_experiment: bool

    def __init__(self, logs: List[LogLine], from_date: datetime, to_date: datetime,
                 from_experiment: bool) -> None:
        self.logs = logs
        self.from_date = from_date
        self.to_date = to_date
        self.from_experiment = from_experiment

    def to_json(self) -> dict:
        return {"logs": [log.to_json() for log in self.logs],
                "from_date": self.from_date,
                "to_date": self.to_date,
                "from_experiment": self.from_experiment}
