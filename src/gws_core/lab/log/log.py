

from datetime import date, datetime, timedelta
from json import loads
from typing import List, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import (LogContext, LogFileLine, Logger,
                                        MessageType)
from gws_core.lab.log.log_dto import (LogCompleteInfoDTO, LogDTO, LogInfo,
                                      LogsBetweenDatesDTO)


class OldLogFileLine(BaseModelDTO):
    """ Type that represent a  the old format of a log line

    :param BaseModelDTO: _description_
    :type BaseModelDTO: _type_
    """
    level: MessageType
    timestamp: str
    message: str
    stack_trace: Optional[str] = None
    scenario_id: Optional[str] = None


class LogLine():
    """Object that represent a line of a log file like
    INFO - 2022-12-08 09:50:05.558872 - START APPLICATION : gws_core version 0.4.0

    or
    INFO - 2022-12-08 09:50:05.558872 - [SCENARIO] - START APPLICATION : gws_core version 0.4.0

    :raises ValueError: _description_
    :return: _description_
    :rtype: _type_
    """

    full_line: str

    level: MessageType
    date_time: datetime
    message: str
    context: LogContext
    context_id: str
    stack_trace: Optional[str] = None

    OLD_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
    OLD_SCENARIO_TEXT = "[SCENARIO]"
    OLD_SEPARATOR = " - "

    def __init__(self, line_str: str) -> None:
        if line_str is None or len(line_str) == 0:
            raise ValueError("line_str is empty")
        self.full_line = line_str

        self.level = None
        self.date_time = None
        self.message = None

        if line_str[0] == '{':
            self._init_new(line_str)
        else:
            self._init_old(line_str)

    def _init_new(self, line_str: str) -> None:
        """
        Read the line as json and extract the level, date, content and if it is from a scenario
        """
        try:
            dict_ = loads(line_str)

            if 'context' in dict_:
                line_json = LogFileLine.from_json(dict_)
                self.level = line_json.level
                self.init_new_date(line_json.timestamp)
                self.message = line_json.message
                self.context = line_json.context
                self.context_id = line_json.context_id
                self.stack_trace = line_json.stack_trace
            else:
                old_line_json = OldLogFileLine.from_json(dict_)
                self.level = old_line_json.level
                self.init_new_date(old_line_json.timestamp)
                self.message = old_line_json.message
                self.context = LogContext.SCENARIO if old_line_json.scenario_id else LogContext.MAIN
                self.context_id = old_line_json.scenario_id
                self.stack_trace = old_line_json.stack_trace

        except ValueError:
            pass

    def _init_old(self, line_str: str) -> None:
        """Read the line and extract the level, date, content and if it is from a scenario
        Line example : INFO - 2023-07-12 14:10:09,676 - Logger configured with log level: INFO
        The log system was changed on v0.5.7

        :param line_str: _description_
        :type line_str: str
        """
        separator = self.OLD_SEPARATOR
        logs_parts = line_str.split(separator)
        self.context = LogContext.MAIN
        self.context_id = None

        if len(logs_parts) >= 3:
            self.level = logs_parts[0]

            self.init_old_date(logs_parts[1])

            self.message = separator.join(logs_parts[2:])

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

    def is_scenario_context(self) -> bool:
        return self.context == LogContext.SCENARIO

    def to_dto(self) -> LogDTO:
        return LogDTO(level=self.level, date_time=self.date_time,
                      message=self.message, context=self.context,
                      context_id=self.context_id, stack_trace=self.stack_trace)

    def to_str(self) -> str:
        return f"{self.date_time} - {self.level} - {self.message}"


class LogCompleteInfo():

    log_info: LogInfo
    content: str

    def __init__(self, log_info: LogInfo, content: str) -> None:
        self.log_info = log_info
        self.content = content

    def get_log_file_date(self) -> date:
        name = self.log_info.name
        return Logger.file_name_to_date(name).date()

    def get_log_lines_by_time(self, start_time: datetime, end_time: datetime,
                              from_scenario_id: str = None,
                              nb_of_lines: int = None) -> List[LogLine]:
        """Filter the log lines by time and if it is from a scenario

        :param start_time: start time of the filter
        :type start_time: datetime
        :param end_time: end time of the filter
        :type end_time: datetime
        :param from_scenario: if provided filter only log with the bool, defaults to None
        :type from_scenario: bool, optional
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

            # if the scenario id is provided, filter the log lines
            # skip lines that are not from the scenario
            # also skip lines that are from another scenario
            if from_scenario_id is not None:
                if not log_line.is_scenario_context() or log_line.context_id != from_scenario_id:
                    continue

            if start_time <= log_line.date_time <= end_time:
                log_lines.append(log_line)

            if nb_of_lines is not None and len(log_lines) >= nb_of_lines:
                stop_date = log_line.get_datetime_without_microseconds()

        return log_lines

    def _get_all_lines(self) -> List[LogLine]:
        log_lines: List[LogLine] = []
        for line in self.content.splitlines():
            if len(line) == 0:
                continue
            log_line = LogLine(line)

            if not log_line.is_valid():
                continue

            log_lines.append(log_line)

        return log_lines

    def get_content_as_dto(self) -> List[LogDTO]:
        lines = self._get_all_lines()

        return [log.to_dto() for log in lines]

    def get_content_as_json(self) -> list:
        lines = self._get_all_lines()

        lines_json = [log.to_dto().to_json_dict() for log in lines]

        return lines_json

    def to_dto(self) -> LogCompleteInfoDTO:
        return LogCompleteInfoDTO(log_info=self.log_info, content=self.get_content_as_dto())


class LogsBetweenDates():

    logs: List[LogLine]
    from_date: datetime
    to_date: datetime
    from_scenario_id: str
    is_last_page: bool

    def __init__(self, logs: List[LogLine], from_date: datetime, to_date: datetime,
                 from_scenario_id: str, is_last_page: bool) -> None:
        self.logs = logs
        self.from_date = from_date
        self.to_date = to_date
        self.from_scenario_id = from_scenario_id
        self.is_last_page = is_last_page

    def to_dto(self) -> LogsBetweenDatesDTO:
        return LogsBetweenDatesDTO(
            logs=[log.to_dto() for log in self.logs],
            from_date=self.from_date,
            to_date=self.to_date,
            from_scenario_id=self.from_scenario_id,
            is_last_page=self.is_last_page
        )

    def get_next_page_date(self) -> datetime:
        """return the start date for the next page
        Add 1 millisecond to the last log date to avoid duplicate logs

        :return: _description_
        :rtype: datetime
        """
        return self.logs[-1].date_time + timedelta(milliseconds=1) if len(self.logs) > 0 else None

    def to_str(self) -> str:
        return "\n".join([log.to_str() for log in self.logs])
