import logging
import sys
from datetime import datetime
from enum import Enum
from logging import Logger as PythonLogger
from logging.handlers import TimedRotatingFileHandler
from os import makedirs, path
from typing import Any, Literal, Optional, cast

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.request_context import RequestContext
from gws_core.core.utils.utils import Utils

LOGGER_NAME = "gws"
LOGGER_FILE_NAME = "log"
RESET_COLOR = "\x1b[0m"

MessageType = Literal["ERROR", "WARNING", "INFO", "DEBUG", "PROGRESS", "EXCEPTION"]

LoggerLevel = Literal["INFO", "DEBUG", "ERROR"]


class LogContext(Enum):
    MAIN = "MAIN"
    SCENARIO = "SCENARIO"
    STREAMLIT = "STREAMLIT"
    REFLEX = "REFLEX"


class LogFileLine(BaseModelDTO):
    level: MessageType
    timestamp: str
    message: str
    stack_trace: str | None = None
    context: LogContext = LogContext.MAIN
    context_id: str | None = None
    instance_id: str | None = None
    request_id: str | None = None


class JSONFormatter(logging.Formatter):
    context: LogContext
    context_id: str | None = None

    def __init__(
        self, context: LogContext = LogContext.MAIN, context_id: str | None = None
    ) -> None:
        super().__init__()
        self.context = context
        self.context_id = context_id

    def format(self, record) -> str:
        log_data = LogFileLine(
            level=cast(MessageType, record.levelname),
            timestamp=Logger.get_date(),
            message=record.getMessage(),
            context=self.context,
            context_id=self.context_id,
            stack_trace=record.exc_text if record.exc_text else None,
            instance_id=getattr(record, "instance_id", None),
            request_id=RequestContext.get_request_id(),
        )
        return log_data.to_json_str(exclude_none=True)


class Logger:
    """
    Logger class

    It logs into the console and in the log file
    """

    FILE_NAME_DATE_FORMAT = "%Y-%m-%d"

    _logger: PythonLogger
    _file_path: str | None = None

    _context: LogContext
    _context_id: str | None = None

    level: LoggerLevel = "INFO"

    # class level
    _waiting_messages: list[dict] = []
    _logger_instance: Optional["Logger"] = None

    def __init__(
        self,
        log_dir: str,
        level: LoggerLevel = "INFO",
        context: LogContext = LogContext.MAIN,
        context_id: str | None = None,
    ) -> None:
        """Create the Gencovery logger, it logs into the console and into a file

        :param log_dir: directory where the logs are stored
        :type log_dir: str
        :param level: level of the logs to show, defaults to "info"
        :type level: error | info | debug, optional
        :param context: context of the logger, defaults to LogContext.MAIN
        :type context: LogContext, optional
        :param context_id: id of the context, defaults to None
        :type context_id: str, optional
        """

        self._context = context
        self._context_id = context_id

        if level is None:
            level = "INFO"
        self.level = level

        if level not in ["ERROR", "INFO", "DEBUG"]:
            raise Exception(
                f"The logging level '{level}' is incorrect, please use one of the following [ERROR, INFO, DEBUG]"
            )

        # Create the logger
        self._logger = logging.getLogger(LOGGER_NAME)

        # Remove any pre-existing handlers (e.g. from a prior init in the same
        # interpreter, or handlers attached by uvicorn/Reflex) so messages are
        # not emitted multiple times with different formatters.
        self._logger.handlers.clear()

        # Don't propagate to the root logger: uvicorn/Reflex configure root
        # handlers that would re-emit our already-formatted message as a new
        # record (showing INFO lines as ERROR, dropping tracebacks, etc.).
        self._logger.propagate = False

        # Set the logger level
        self._logger.setLevel(level)

        # Format of the logs, format date like : 2024-06-24T14:18:07.442618+00:00
        formatter = logging.Formatter("%(levelname)s - %(asctime)s - %(message)s")

        # Configure the console logger. Write to the *original* stderr
        # (sys.__stderr__) rather than sys.stderr, because Reflex/uvicorn
        # replace sys.stderr with a line-based interceptor that re-emits each
        # line as its own ERROR record and drops everything after the first
        # newline — which is why multi-line tracebacks don't reach the console.
        console_logger = logging.StreamHandler(sys.stdout)
        console_logger.setFormatter(formatter)
        self._logger.addHandler(console_logger)

        # Configure the logs into the log files
        if not path.exists(log_dir):
            makedirs(log_dir)
        self._file_path = path.join(log_dir, LOGGER_FILE_NAME)
        # file_handler = logging.FileHandler(Logger._file_path)

        # define a TimeRotating file to create a new file each day à 00:00
        # this write the log in a file with a json format
        file_handler = TimedRotatingFileHandler(self._file_path, when="midnight")
        file_handler.setFormatter(JSONFormatter(context=context, context_id=context_id))
        # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

    @classmethod
    def build_main_logger(
        cls,
        log_dir: str,
        level: LoggerLevel = "INFO",
        context: LogContext = LogContext.MAIN,
        context_id: str | None = None,
    ) -> "Logger":
        cls.clear_logger()
        logger = Logger(log_dir, level, context, context_id)
        cls._logger_instance = logger

        cls._log_waiting_message()

        return logger

    @classmethod
    def check_log_level(cls, log_level: str) -> LoggerLevel:
        if not log_level:
            return "INFO"
        if not Utils.value_is_in_literal(log_level, LoggerLevel):
            raise Exception(
                f"The logging level '{log_level}' is incorrect, please use one of the following [INFO, DEBUG, ERROR]"
            )
        return cast(LoggerLevel, log_level)

    @classmethod
    def error(
        cls, message: str, exception: Exception | None = None, instance_id: str | None = None
    ) -> None:
        cls._log_message("ERROR", message, instance_id=instance_id)
        if exception:
            cls.log_exception_stack_trace(exception, instance_id=instance_id)

    @classmethod
    def log_exception_stack_trace(
        cls, exception: Exception, instance_id: str | None = None
    ) -> None:
        cls._log_message("EXCEPTION", exception, instance_id=instance_id)

    @classmethod
    def warning(cls, message: str) -> None:
        cls._log_message("WARNING", message)

    @classmethod
    def info(cls, message: str) -> None:
        cls._log_message("INFO", message)

    @classmethod
    def debug(cls, message: str) -> None:
        cls._log_message("DEBUG", message)

    @classmethod
    def progress(cls, message: str) -> None:
        cls._log_message("PROGRESS", message)

    @classmethod
    def get_file_path(cls) -> str | None:
        return cls._file_path

    @classmethod
    def get_instance(cls) -> "Logger":
        if cls._logger_instance is None:
            raise Exception("Logger instance is not initialized")
        return cls._logger_instance

    @classmethod
    def _log_message(
        cls, level_name: MessageType, obj: Any, instance_id: str | None = None
    ) -> None:
        """Log a message

        :param level_name: level of the message
        :type level_name: str
        :param obj: message or exception to log
        :type obj: Any
        :param instance_id: optional instance id to include in the log
        :type instance_id: str | None
        """
        if cls._logger_instance:
            logger = cls._logger_instance

            if level_name == "EXCEPTION":
                logger._log_exception(obj, instance_id)
                return

            if level_name == "ERROR":
                logger._log_error(obj, instance_id)
            elif level_name == "WARNING":
                logger._log_warning(obj)
            elif level_name in {"INFO", "PROGRESS"}:
                logger._log_info(obj)
            elif level_name == "DEBUG":
                logger._log_debug(obj)

        else:
            # add the message in the waiting list to be logged later
            cls._waiting_messages.append(
                {"level_name": level_name, "obj": obj, "instance_id": instance_id}
            )

    @classmethod
    def _log_waiting_message(cls) -> None:
        """Log all the waiting messages"""
        for message in cls._waiting_messages:
            cls._log_message(
                message["level_name"], message["obj"], instance_id=message["instance_id"]
            )
        cls._waiting_messages = []

    # Get the current date in Human readable format
    @classmethod
    def get_date(cls) -> str:
        current_date: datetime = DateHelper.now_utc()
        return current_date.isoformat()

    @classmethod
    def print_sql_queries(cls) -> None:
        """If call the sql queries will be printed in the console"""
        logger = logging.getLogger("peewee")
        logger.addHandler(logging.StreamHandler())
        logger.setLevel(logging.DEBUG)

    @classmethod
    def date_to_file_name(cls, date: datetime) -> str:
        """Convert a date to a file name.
        If the date is the current date the file name is 'log'
        Otherwise the file name is in the format 'log.YYYY-MM-DD'

        :param date: date to convert
        :type date: datetime
        :return: the file name
        :rtype: str
        """

        if DateHelper.are_same_day(date, DateHelper.now_utc()):
            return "log"

        return "log." + date.strftime(cls.FILE_NAME_DATE_FORMAT)

    @classmethod
    def file_name_to_date(cls, file_name: str) -> datetime:
        """Convert a file name to a date.
        If the file name is 'log' the current date is returned
        Otherwise file name must be in the format 'log.YYYY-MM-DD'

        :param file_name: file name to convert
        :type file_name: str
        :return: the date
        :rtype: datetime
        """
        if file_name == "log":
            return DateHelper.now_utc()

        return DateHelper.from_str(file_name.split(".")[1], "%Y-%m-%d")

    @classmethod
    def clear_logger(cls) -> None:
        """Clear the logger"""
        if cls._logger_instance:
            cls._logger_instance._clear()
            cls._logger_instance = None

    @classmethod
    def is_debug_level(cls) -> bool:
        """Check if the logger is in debug level

        :return: True if the logger is in debug level, False otherwise
        :rtype: bool
        """
        return bool(cls._logger_instance and cls._logger_instance.level == "DEBUG")

    def _clear(self) -> None:
        self._logger.handlers.clear()

    def _log_exception(self, exception: Exception, instance_id: str | None = None) -> None:
        self._logger.exception(
            str(exception), exc_info=exception, extra={"instance_id": instance_id}
        )

    def _log_error(self, message: str, instance_id: str | None = None) -> None:
        self._logger.error(message, extra={"instance_id": instance_id})

    def _log_warning(self, message: str) -> None:
        self._logger.warning(message)

    def _log_info(self, message: str) -> None:
        self._logger.info(message)

    def _log_debug(self, message: str) -> None:
        self._logger.debug(message)
