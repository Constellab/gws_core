# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import logging
from datetime import datetime
from logging import Logger as PythonLogger
from logging.handlers import TimedRotatingFileHandler
from os import makedirs, path
from typing import Any, Literal

from gws_core.core.utils.date_helper import DateHelper

from ..exception.exceptions.bad_request_exception import BadRequestException
from .settings import Settings

LOGGER_NAME = "gws"
LOGGER_FILE_NAME = "log"
RESET_COLOR = "\x1b[0m"

MessageType = Literal['ERROR', 'WARNING', 'INFO', 'DEBUG', 'PROGRESS', 'EXCEPTION']


class Logger:
    """
    Logger class

    It logs into the console and in the log file
    """

    SUB_PROCESS_TEXT = "[EXPERIMENT]"
    SEPARATOR = " - "
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
    FILE_NAME_DATE_FORMAT = "%Y-%m-%d"

    _logger: PythonLogger = None
    _file_path: str = None
    _is_experiment_process: bool = None

    _waiting_messages: list = []

    def __init__(self, level: Literal["ERROR", "INFO", "DEBUG"] = "INFO", _is_experiment_process: bool = False):
        """Create the Gencovery logger, it logs into the console and into a file

        :param level: level of the logs to show, defaults to "info"
        :type level: error | info | debug, optional
        :param _is_experiment_process: set to true when the gws is runned inside a subprocess
        (like when running a experiment in another process), defaults to False
        :type _is_experiment_process: bool, optional
        """
        if Logger._logger is not None:
            return
            #raise BadRequestException("The logger already exists")

        Logger._is_experiment_process = _is_experiment_process

        if level not in ["ERROR", "INFO", "DEBUG"]:
            raise BadRequestException(
                f"The logging level '{level}' is incorrect, please use one of the following [ERROR, INFO, DEBUG]")

        # Create the logger
        Logger._logger = logging.getLogger(LOGGER_NAME)

        # Set the logger level
        Logger._logger.setLevel(level)

        # Format of the logs
        formatter = logging.Formatter("%(message)s")

        # Configure the console logger
        console_logger = logging.StreamHandler()
        console_logger.setFormatter(formatter)
        Logger._logger.addHandler(console_logger)

        # Configure the logs into the log files
        settings = Settings.get_instance()

        log_dir = settings.get_log_dir()
        if not path.exists(log_dir):
            makedirs(log_dir)
        Logger._file_path = path.join(log_dir, LOGGER_FILE_NAME)
        # file_handler = logging.FileHandler(Logger._file_path)

        # define a TimeRotating file to create a new file each day à 00:00
        file_handler = TimedRotatingFileHandler(
            Logger._file_path, when="midnight")
        file_handler.setFormatter(formatter)
        Logger._logger.addHandler(file_handler)

        if _is_experiment_process:
            Logger.info("Sub process started")
        else:
            Logger.info(
                f"START APPLICATION : {settings.name} version {settings.version}, log level: {level}")

        self._log_waiting_message()

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

            complete_message = cls._get_message(level_name, obj)
            if level_name == "ERROR":
                cls._logger.error(complete_message)
            elif level_name == "WARNING":
                cls._logger.warning(complete_message)
            elif level_name == "INFO" or level_name == "PROGRESS":
                cls._logger.info(complete_message)
            elif level_name == "DEBUG":
                cls._logger.debug(complete_message)

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

    @classmethod
    def _get_message(cls, level_name: str, message: str) -> str:
        # get the annoted text for Sub process logs
        sub_process_text: str = f"{cls.SEPARATOR}{cls.SUB_PROCESS_TEXT}" if cls._is_experiment_process else ""

        return f"{level_name}{cls.SEPARATOR}{cls._get_date()}{sub_process_text}{cls.SEPARATOR}{message}"

    # Get the current date in Human readable format
    @classmethod
    def _get_date(cls) -> str:
        current_date: datetime = DateHelper.now_utc()
        return current_date.strftime(cls.DATE_FORMAT)

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
