import os
from datetime import datetime

from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.logger import LogContext, Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper
from gws_core.lab.log.log_dto import LogInfo, LogsStatusDTO
from gws_core.space.mail_service import MailService
from gws_core.user.current_user_service import CurrentUserService

from .log import LogCompleteInfo, LogLine, LogsBetweenDates


class LogService:
    @classmethod
    def get_logs_status(cls) -> LogsStatusDTO:
        log_folder = Settings.get_instance().get_log_dir()
        log_status: LogsStatusDTO = LogsStatusDTO(log_folder=log_folder, log_files=[])

        for node_name in os.listdir(log_folder):
            log_info = cls.get_log_info(node_name)

            if log_info is not None:
                log_status.log_files.append(log_info)

        # sort logs_files by name in reverse but keep the last log file named 'log' at the top
        log_status.log_files.sort(key=lambda log: log.name, reverse=True)
        log_status.log_files.sort(key=lambda log: log.name == "log", reverse=True)

        return log_status

    @classmethod
    def get_log_complete_info(cls, node_name: str) -> LogCompleteInfo:
        log_info = cls.get_log_info(node_name)

        if log_info is None:
            raise BadRequestException(f"File '{node_name}' is not a log file")

        log_folder = Settings.get_instance().get_log_dir()
        log_file_path = os.path.join(log_folder, node_name)

        with open(log_file_path, encoding="UTF-8") as f:
            content = f.read()

        return LogCompleteInfo(log_info, content)

    @classmethod
    def get_log_info(cls, node_name: str) -> LogInfo | None:
        log_folder = Settings.get_instance().get_log_dir()

        if not node_name.startswith("log"):
            return None

        log_file_path = os.path.join(log_folder, node_name)
        if not FileHelper.is_file(log_file_path):
            return None

        return LogInfo(
            name=node_name,
            file_size=FileHelper.get_size(log_file_path),
        )

    @classmethod
    def get_logs_between_dates(
        cls,
        from_date: datetime,
        to_date: datetime,
        context: LogContext | None = None,
        context_id: str | None = None,
        nb_of_lines: int = 100,
    ) -> LogsBetweenDates:
        log_lines: list[LogLine] = []

        # retrieve logs for each day
        for date in DateHelper.date_range(from_date, to_date, include_end_date=True):
            one_day_from: datetime | None = None
            one_day_to: datetime | None = None
            # if the from_date is the same day as the date, we use the from_date
            # otherwise with use the date at 00:00:00
            if DateHelper.are_same_day(from_date, date):
                one_day_from = DateHelper.convert_datetime_to_utc(from_date)
            else:
                one_day_from = DateHelper.convert_datetime_to_utc(
                    datetime(year=date.year, month=date.month, day=date.day)
                )

            # if the to_date is the same day as the date, we use the to_date
            # otherwise with use the date at 23:59:59
            if DateHelper.are_same_day(to_date, date):
                one_day_to = DateHelper.convert_datetime_to_utc(to_date)
            else:
                one_day_to = DateHelper.convert_datetime_to_utc(
                    datetime(
                        year=date.year,
                        month=date.month,
                        day=date.day,
                        hour=23,
                        minute=59,
                        second=59,
                    )
                )

            try:
                log_lines.extend(
                    cls.get_logs_between_dates_same_day(
                        one_day_from, one_day_to, context, context_id, nb_of_lines - len(log_lines)
                    )
                )
            # skip error : file is not log file
            except BadRequestException:
                continue

            # if we have enough lines, we stop
            if len(log_lines) >= nb_of_lines:
                break

        return LogsBetweenDates(
            logs=log_lines,
            from_date=from_date,
            to_date=to_date,
            context=context,
            context_id=context_id,
            is_last_page=len(log_lines) < nb_of_lines,
        )

    @classmethod
    def get_logs_between_dates_same_day(
        cls,
        from_date: datetime,
        to_date: datetime,
        context: LogContext | None = None,
        context_id: str | None = None,
        nb_of_lines: int = 100,
    ) -> list[LogLine]:
        if not DateHelper.are_same_day(from_date, to_date):
            raise BadRequestException("The dates must be on the same day")

        log_file_name = Logger.date_to_file_name(from_date)

        log_complete_info = cls.get_log_complete_info(log_file_name)
        return log_complete_info.get_log_lines_by_time(
            from_date, to_date, context, context_id, nb_of_lines
        )

    @classmethod
    def send_log_to_support(cls, request_id: str) -> bool:
        """Retrieve all log lines for the request_id from today's log and send them to support via email.

        :param request_id: the request ID to look up in today's logs
        :type request_id: str
        :raises BadRequestException: if no request_id is provided or no log found for the request_id
        :return: True if the mail was sent successfully
        :rtype: bool
        """
        if not request_id:
            raise BadRequestException("A request_id is required to send logs to support")

        today_log_file_name = Logger.date_to_file_name(DateHelper.now_utc())
        log_complete_info = cls.get_log_complete_info(today_log_file_name)

        log_lines = log_complete_info.get_log_lines_by_request_id(request_id)

        if not log_lines:
            raise BadRequestException(
                f"No log lines found today for request_id '{request_id}'"
            )

        # Find the first error log line to use as main context
        error_line = next(
            (line for line in log_lines if line.level in ("ERROR", "EXCEPTION")),
            None,
        )

        # Retrieve current user info
        current_user = CurrentUserService.get_and_check_current_user()

        # Retrieve lab info
        lab_id = Settings.get_lab_id()
        lab_name = Settings.get_lab_name()

        log_lines_str = "\n".join([line.to_str() for line in log_lines])

        subject = f"Log report for request {request_id}"

        # Build header context
        content = "<h3>Log Report</h3>"

        if error_line and error_line.message:
            content += f"<p><strong>Error:</strong> {error_line.message}</p>"

        content += (
            f"<p><strong>Request ID:</strong> {request_id}</p>"
            f"<p><strong>Lab:</strong> {lab_name} (ID: {lab_id})</p>"
            f"<p><strong>User:</strong> {current_user.first_name} {current_user.last_name} "
            f"(ID: {current_user.id}, Email: {current_user.email})</p>"
        )

        if error_line and error_line.instance_id:
            content += f"<p><strong>Instance ID:</strong> {error_line.instance_id}</p>"

        # Complete log lines
        content += (
            f"<p><strong>Number of log lines:</strong> {len(log_lines)}</p>"
            f"<h4>Complete log lines for this request:</h4>"
            f"<pre>{log_lines_str}</pre>"
        )

        return MailService.send_mail_to_support(content=content, subject=subject)

    @classmethod
    def get_log_file_path(cls, node_name: str) -> str:
        log_info = cls.get_log_info(node_name)

        if log_info is None:
            raise BadRequestException(f"File {node_name} is not a log file")

        return os.path.join(Settings.get_instance().get_log_dir(), node_name)
