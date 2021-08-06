# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import logging
import traceback
from datetime import date, datetime
from logging import Logger as PythonLogger
from logging.handlers import TimedRotatingFileHandler
from os import makedirs, path
from typing import Literal

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException

from .settings import Settings

LOGGER_NAME = "gws"
LOGGER_FILE_NAME = "log"
RESET_COLOR = "\x1b[0m"


class Logger:
    """
    Logger class

    It logs into the console and in the log file
    """

    _logger: PythonLogger = None
    _file_path: str = None
    _is_experiment_process: bool = None

    def __init__(self, level: Literal["ERROR", "INFO", "DEBUG"] = "INFO", _is_experiment_process: bool = False):
        """Create the Gencovery logger, it logs into the console and into a file

        :param level: level of the logs to show, defaults to "info"
        :type level: error | info | debug, optional
        :param _is_experiment_process: set to true when the gws is runned inside a subprocess
        (like when running a experiment in another process), defaults to False
        :type _is_experiment_process: bool, optional
        """
        Logger._is_experiment_process = _is_experiment_process

        if Logger._logger is not None:
            raise BadRequestException("The logger already exists")

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
        settings = Settings()

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

    # -- E --

    @classmethod
    def error(cls, message: str) -> None:
        cls._logger.error(cls._get_message("ERROR", message))

    # todo fix method
    @classmethod
    def log_exception_stack_trace(cls) -> None:
        cls._logger.error(traceback.print_exc())

    @classmethod
    def warning(cls, message: str) -> None:
        cls._logger.warning(cls._get_message("WARNING", message))

    @classmethod
    def info(cls, message: str) -> None:
        cls._logger.info(cls._get_message("INFO", message))

    @classmethod
    def debug(cls, message: str) -> None:
        cls._logger.debug(cls._get_message("DEBUG", message))

    # -- P --

    @classmethod
    def progress(cls, message: str) -> None:
        cls._logger.info(cls._get_message("PROGRESS", message))

    # -- F --

    @classmethod
    def get_file_path(cls) -> str:
        return cls._file_path

    @classmethod
    def get_sub_process_text(cls) -> str:
        """return the text to annotated the sub process logs
        """
        return "[EXPERIMENT]"

    # -- I --

    # -- S --

    @classmethod
    def _get_message(cls, level_name: str, message: str) -> str:
        # get the annoted text for Sub process logs
        sub_process_text: str = f"{cls.get_sub_process_text()} -" if cls._is_experiment_process else ""
        return f"{level_name} - {cls._get_date()} - {sub_process_text} {message}"

    # Get the current date in Human readable format
    @classmethod
    def _get_date(cls) -> str:
        current_date: datetime = datetime.now()
        return current_date.strftime("%Y-%m-%d %H:%M:%S.%f")
