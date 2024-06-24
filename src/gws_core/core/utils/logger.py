

import logging
from datetime import datetime
from logging import Logger as PythonLogger
from logging.handlers import TimedRotatingFileHandler
from os import makedirs, path
from typing import Any, Literal, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.date_helper import DateHelper
from gws_core.core.utils.utils import Utils

from ..exception.exceptions.bad_request_exception import BadRequestException

LOGGER_NAME = "gws"
LOGGER_FILE_NAME = "log"
RESET_COLOR = "\x1b[0m"

MessageType = Literal['ERROR', 'WARNING', 'INFO', 'DEBUG', 'PROGRESS', 'EXCEPTION']

LoggerLevel = Literal['INFO', 'DEBUG', 'ERROR']


class LogFileLine(BaseModelDTO):
    level: MessageType
    timestamp: str
    message: str
    experiment_id: Optional[str] = None
    stack_trace: Optional[str] = None


class JSONFormatter(logging.Formatter):

    experiment_id: str = None

    def __init__(self, experiment_id: str = None):
        super().__init__()
        self.experiment_id = experiment_id

    def format(self, record) -> str:
        log_data = LogFileLine(
            level=record.levelname,
            timestamp=Logger.get_date(),
            message=record.getMessage(),
            experiment_id=self.experiment_id,
            stack_trace=record.exc_text if record.exc_text else None
        )
        return log_data.to_json_str()


class Logger:
    """
    Logger class

    It logs into the console and in the log file
    """

    SUB_PROCESS_TEXT = "[EXPERIMENT]"
    SEPARATOR = " - "
    FILE_NAME_DATE_FORMAT = "%Y-%m-%d"

    _logger: PythonLogger = None
    _file_path: str = None
    _experiment_id: str = None

    _waiting_messages: list = []

    def __init__(self, log_dir: str = None,
                 level: LoggerLevel = "INFO", experiment_id: str = None) -> None:
        """Create the Gencovery logger, it logs into the console and into a file

        :param level: level of the logs to show, defaults to "info"
        :type level: error | info | debug, optional
        :param _experiment_id: set when  gws is runned inside a subprocess to run an experiment, defaults to False
        :type _experiment_id: bool, optional
        """
        if Logger._logger is not None:
            return
            # raise BadRequestException("The logger already exists")

        Logger._experiment_id = experiment_id

        if level is None:
            level = "INFO"

        if level not in ["ERROR", "INFO", "DEBUG"]:
            raise BadRequestException(
                f"The logging level '{level}' is incorrect, please use one of the following [ERROR, INFO, DEBUG]")

        # Create the logger
        Logger._logger = logging.getLogger(LOGGER_NAME)

        # Set the logger level
        Logger._logger.setLevel(level)

        # Format of the logs, format date like : 2024-06-24T14:18:07.442618+00:00
        formatter = logging.Formatter("%(levelname)s - %(asctime)s - %(message)s")

        # Configure the console logger
        console_logger = logging.StreamHandler()
        console_logger.setFormatter(formatter)
        Logger._logger.addHandler(console_logger)

        # Configure the logs into the log files
        if not path.exists(log_dir):
            makedirs(log_dir)
        Logger._file_path = path.join(log_dir, LOGGER_FILE_NAME)
        # file_handler = logging.FileHandler(Logger._file_path)

        # define a TimeRotating file to create a new file each day à 00:00
        # this write the log in a file with a json format
        file_handler = TimedRotatingFileHandler(
            Logger._file_path, when="midnight")
        file_handler.setFormatter(JSONFormatter(Logger._experiment_id))
        # formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # file_handler.setFormatter(formatter)
        Logger._logger.addHandler(file_handler)

        if experiment_id:
            Logger.info(f"Logger configured for experiment process with log level: {level}")
        else:
            Logger.info(f"Logger configured with log level: {level}")

        self._log_waiting_message()

    @classmethod
    def check_log_level(cls, log_level: str) -> LoggerLevel:
        if not log_level:
            return "INFO"
        if not Utils.value_is_in_literal(log_level, LoggerLevel):
            raise BadRequestException(
                f"The logging level '{log_level}' is incorrect, please use one of the following [INFO, DEBUG, ERROR]")
        return log_level

    @classmethod
    def error(cls, message: str) -> None:
        cls._log_message("ERROR", message)

    @classmethod
    def log_exception_stack_trace(cls, exception: Exception) -> None:
        cls._log_message('EXCEPTION', exception)

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
    def get_file_path(cls) -> str:
        return cls._file_path

    @classmethod
    def _log_message(cls, level_name: MessageType, obj: Any) -> None:
        """Log a message

        :param level_name: level of the message
        :type level_name: str
        :param message: message to log
        :type message: str
        """
        if cls._logger:

            if level_name == "EXCEPTION":
                cls._logger.exception(obj, exc_info=True)
                return

            if level_name == "ERROR":
                cls._logger.error(obj)
            elif level_name == "WARNING":
                cls._logger.warning(obj)
            elif level_name == "INFO" or level_name == "PROGRESS":
                cls._logger.info(obj)
            elif level_name == "DEBUG":
                cls._logger.debug(obj)

        else:
            # add the message in the waiting list to be logged later
            cls._waiting_messages.append({"level_name": level_name, "obj": obj})

    @classmethod
    def _log_waiting_message(cls) -> None:
        """Log all the waiting messages
        """
        for message in cls._waiting_messages:
            cls._log_message(message['level_name'], message['obj'])
        cls._waiting_messages = []

    # Get the current date in Human readable format

    @classmethod
    def get_date(cls) -> str:
        current_date: datetime = DateHelper.now_utc()
        return current_date.isoformat()

    @classmethod
    def print_sql_queries(cls) -> None:
        """If call the sql queries will be printed in the console
        """
        logger = logging.getLogger('peewee')
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
            return 'log'

        return 'log.' + date.strftime(cls.FILE_NAME_DATE_FORMAT)

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
        if file_name == 'log':
            return DateHelper.now_utc()

        return DateHelper.from_str(file_name.split(".")[1], "%Y-%m-%d")

    @classmethod
    def clear_logger(cls) -> None:
        """Clear the logger
        """
        Logger._file_path = None
        Logger._experiment_id = None
        Logger._logger.handlers.clear()
        Logger._logger = None
