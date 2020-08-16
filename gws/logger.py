
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
        settings = Settings.retrieve()
        self._is_test = is_test

        log_dir = settings.get_log_dir()
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self._file_path = os.path.join(log_dir, LOGGER_FILE_NAME)

        fh = logging.FileHandler(self._file_path)
        self._logger = logging.getLogger(LOGGER_NAME)
        self._logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(" %(message)s")
        fh.setFormatter(formatter)
        self._logger.addHandler(fh)

        if is_new_session:
            self._logger.info("\nSession: " + str(datetime.datetime.now()) + "\n")
    
    # -- E --

    def error(self,message, *args, **kwargs):
        self._logger.error(f"{datetime.datetime.now().time()}: {message}", *args, **kwargs)
        if self._is_test:
            print(message)

    # -- F --

    @property
    def file_path(self):
        return self._file_path

    # -- I --

    def info(self, message, *args, **kwargs):
        self._logger.info(f"{datetime.datetime.now().time()}: {message}", *args, **kwargs)
        if self._is_test:
            print(message)

    
    # -- W --

    def warning(self,message, *args, **kwargs):
        self._logger.warning(f"{datetime.datetime.now().time()}: {message}", *args, **kwargs)
        if self._is_test:
            print(message)