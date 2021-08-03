# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import datetime
import logging
import os
import traceback

from .settings import Settings

LOGGER_NAME = "gws"
LOGGER_FILE_NAME = str(datetime.date.today()) + ".log"
RESET_COLOR = "\x1b[0m"


class Logger:
    """
    Logger class

    It logs into the console and in the log file
    """

    _logger = None
    _is_debug = None
    _file_path = None

    def __init__(self, is_new_session=False, is_debug: bool = None):
        is_debug = True
        if Logger._logger is None:
            if not is_debug is None:
                Logger._is_debug = is_debug
            # Create the logger
            Logger._logger = logging.getLogger(LOGGER_NAME)
            # Format of the logs
            formatter = logging.Formatter(
                "%(message)s ")

            # Configure the console logger
            console_logger = logging.StreamHandler()
            console_logger.setFormatter(formatter)
            Logger._logger.addHandler(console_logger)

            # Configure the logs into the log files
            settings = Settings()

            log_dir = settings.get_log_dir()
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            Logger._file_path = os.path.join(log_dir, LOGGER_FILE_NAME)
            file_handler = logging.FileHandler(Logger._file_path)
            Logger._logger.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            Logger._logger.addHandler(file_handler)

            if is_new_session:
                Logger._logger.info(
                    f"START APPLICATION : {settings.name} version {settings.version} \n")

    # -- E --

    @classmethod
    def error(cls, message: str) -> None:
        if not cls._logger:
            Logger()
        cls._logger.error(cls._get_message("ERROR", message))

    @classmethod
    def log_exception_stack_trace(cls) -> None:
        if not cls._logger:
            Logger()
        cls._logger.error(traceback.print_exc())

    @classmethod
    def warning(cls, message: str) -> None:
        if not cls._logger:
            Logger()
        cls._logger.warning(cls._get_message("WARNING", message))

    @classmethod
    def info(cls, message: str) -> None:
        if not cls._logger:
            Logger()
        cls._logger.info(cls._get_message("INFO", message))

    # -- P --

    @classmethod
    def progress(cls, message: str) -> None:
        if not cls._logger:
            Logger()
        cls._logger.info(cls._get_message("PROGRESS", message))
        try:
            from .progress_bar import ProgressBar
            ProgressBar.get_current_progress_bar().add_message(message)
        except:
            pass

    # -- F --

    @classmethod
    def get_file_path(cls) -> str:
        if not cls._logger:
            Logger()
        return cls._file_path

    # -- I --

    @classmethod
    def is_debug(cls) -> bool:
        if cls._is_debug is None:
            settings = Settings.retrieve()
            cls._is_debug = settings.is_debug
        return cls._is_debug

    # -- S --

    @classmethod
    def _get_message(cls, level_name: str, message: str) -> str:
        return f"{level_name} - {cls._get_date()} - {message}"

    # Get the current date in Human readable format
    @classmethod
    def _get_date(cls) -> str:
        current_date: datetime.datetime = datetime.datetime.now()
        return current_date.strftime("%Y-%m-%d %H:%M:%S.%f")
