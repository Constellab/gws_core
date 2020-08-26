
import os
import logging
import datetime
from gws.settings import Settings

LOGGER_NAME = "gws"
LOGGER_FILE_NAME = str(datetime.date.today()) + ".log"

class Logger:
    _logger = None
    _is_test = False
    _file_path = None

    def __init__(self, is_new_session = False, is_test=False):
        cls = Logger
        if cls._logger is None:
            settings = Settings.retrieve()
            cls._is_test = is_test

            log_dir = settings.get_log_dir()
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            cls._file_path = os.path.join(log_dir, LOGGER_FILE_NAME)

            fh = logging.FileHandler(cls._file_path)
            cls._logger = logging.getLogger(LOGGER_NAME)
            cls._logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter(" %(message)s")
            fh.setFormatter(formatter)
            cls._logger.addHandler(fh)

            if is_new_session:
                cls._logger.info("\nSession: " + str(datetime.datetime.now()) + "\n")

    # -- E --

    @classmethod
    def error(cls, message, *args, **kwargs):
        Logger()
        cls._logger.error(f"ERROR: {datetime.datetime.now().time()}: {message}", *args, **kwargs)
        if isinstance(message, Exception):
            raise message
        

    # -- F --

    @classmethod
    def get_file_path(cls):
        Logger()
        return cls._file_path

    # -- I --

    @classmethod
    def info(cls, message, *args, **kwargs):
        Logger()
        cls._logger.info(f"INFO: {datetime.datetime.now().time()}: {message}", *args, **kwargs)
        if cls._is_test:
            print(message)

    
    # -- W --

    @classmethod
    def warning(cls,message, *args, **kwargs):
        Logger()
        cls._logger.warning(f"WARNING: {datetime.datetime.now().time()}: {message}", *args, **kwargs)
        if cls._is_test:
            print(message)