# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import os
import logging
import datetime
from gws.settings import Settings

LOGGER_NAME = "gws"
LOGGER_FILE_NAME = str(datetime.date.today()) + ".log"

class Logger:
    """
    Logger class
    """

    _logger = None
    _is_debug = None
    _file_path = None
    
    def __init__(self, is_new_session = False, is_debug: bool = None):

        if Logger._logger is None:
            if not is_debug is None:
                Logger._is_debug = is_debug
            
            settings = Settings()
            log_dir = settings.get_log_dir()
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            Logger._file_path = os.path.join(log_dir, LOGGER_FILE_NAME)

            fh = logging.FileHandler(Logger._file_path)
            Logger._logger = logging.getLogger(LOGGER_NAME)
            Logger._logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter(" %(message)s")
            fh.setFormatter(formatter)
            Logger._logger.addHandler(fh)

            if is_new_session:
                Logger._logger.info("\nSESSION: " + str(datetime.datetime.now()) + "\n")
    
    # -- E --

    @classmethod
    def error(cls, message):
        if not cls._logger:
            Logger()
            
        cls._logger.error(f"ERROR: {datetime.datetime.now().time()} -- {message}")
        cls._print(message)
            
    # -- F --

    @classmethod
    def get_file_path(cls):
        if not cls._logger:
            Logger()
            
        return cls._file_path

    # -- I --

    @classmethod
    def is_debug(cls):
        if cls._is_debug is None:
            settings = Settings.retrieve()
            cls._is_debug = settings.is_debug
        
        return cls._is_debug
        
    @classmethod
    def info(cls, message):
        if not cls._logger:
            Logger()
            
        cls._logger.info(f"INFO: {datetime.datetime.now().time()} -- {message}")
        cls._print(message)
    
    # -- P --

    @classmethod
    def _print(cls, message):
        erase = '\x1b[1A\x1b[2K'
        if cls.is_debug():
            print(message)
        else:
            print(erase + message)

    # -- S --
   
    # -- W --

    @classmethod
    def warning(cls, message):
        if not cls._logger:
            Logger()
            
        cls._logger.warning(f"WARNING: {datetime.datetime.now().time()} # {message}")
        cls._print(message)
            

class Error(Exception):
    """
    Error class
    """

    message = ""
    def __init__(self, message, *args):
        if args:
            exc_message = f"({message}, {', '.join(args)})"
        else:
            exc_message = message
            
        super().__init__(exc_message)
        
        self.message = exc_message
        Logger.error(exc_message)

class Warning():
    """
    Warning class
    """

    message = ""
    
    def __init__(self, message, *args, stdout: bool=False):
        if args:
            exc_message = f"({message}, {', '.join(args)})"
        else:
            exc_message = message
        
        self.message = exc_message
        Logger.warning(exc_message)

        if stdout:
            print(exc_message)
        
class Info():
    """
    Info class
    """

    message = ""
    def __init__(self, message, *args, stdout: bool=False):
        if args:
            exc_message = f"({message}, {', '.join(args)})"
        else:
            exc_message = message
        
        self.message = exc_message
        Logger.info(exc_message)

        if stdout:
            print(exc_message)