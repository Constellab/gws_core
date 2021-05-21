
import os
import logging
import datetime
from gws.settings import Settings

LOGGER_NAME = "gws"
LOGGER_FILE_NAME = str(datetime.date.today()) + ".log"

class Logger:
    _logger = None
    _is_debug = None
    _is_test = None
    _file_path = None
    show_all = False
    
    def __init__(self, is_new_session = False, is_test: bool = None, is_debug: bool = None):

        if Logger._logger is None:
            
            if not is_test is None:
                Logger._is_test = is_test
                
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
                Logger._logger.info("\nSession: " + str(datetime.datetime.now()) + "\n")
    
    # -- E --

    @classmethod
    def error(cls, message):
        if not cls._logger:
            Logger()
            
        cls._logger.error(f"ERROR: {datetime.datetime.now().time()} -- {message}")
        if cls.is_test() or cls.is_debug() or cls.show_all:
            if cls.is_debug():
                #-> keep all log track on screen
                print(message)  
            else:
                #-> keep only on line
                print('\x1b[2K', end='\r')
                print(message, end='\r')
            

    # -- F --

    @classmethod
    def get_file_path(cls):
        if not cls._logger:
            Logger()
            
        return cls._file_path

    # -- I --
    
    @classmethod
    def is_test(cls):
        if cls._is_test is None:
            settings = Settings.retrieve()
            cls._is_test = settings.is_test
        
        return cls._is_test
    
    @classmethod
    def is_debug(cls):
        if cls.is_test() is None:
            settings = Settings.retrieve()
            cls._is_debug = settings.is_debug
        
        return cls._is_debug
        
    @classmethod
    def info(cls, message):
        if not cls._logger:
            Logger()
            
        cls._logger.info(f"INFO: {datetime.datetime.now().time()} -- {message}")
        if cls.is_test() or cls.is_debug() or cls.show_all:
            if cls.is_debug():
                #-> keep all log track on screen
                print(message)  
            else:
                #-> keep only on line
                print('\x1b[2K', end='\r')
                print(message, end='\r')
    
    # -- S --
    
    def __str__(self):
        return 
    
    # -- W --

    @classmethod
    def warning(cls, message):
        if not cls._logger:
            Logger()
            
        cls._logger.warning(f"WARNING: {datetime.datetime.now().time()} # {message}")
        if cls.is_test() or cls.is_debug() or cls.show_all:
            if cls.is_debug():
                #-> keep all log track on screen
                print(message)  
            else:
                #-> keep only on line
                print('\x1b[2K', end='\r')
                print(message, end='\r')
            

class Error(Exception):
    message = ""
    def __init__(self, message, *args):
        if len(args):
            exc_message = f"({message}, {', '.join(args)})"
        else:
            exc_message = message
            
        super().__init__(exc_message)
        
        self.message = exc_message
        Logger.error(exc_message)

class Warning():
    message = ""
    
    def __init__(self, message, *args):
        if len(args):
            exc_message = f"({message}, {', '.join(args)})"
        else:
            exc_message = message
        
        self.message = exc_message
        Logger.warning(exc_message)
        
class Info():
    message = ""
    def __init__(self, message, *args):
        if len(args):
            exc_message = f"({message}, {', '.join(args)})"
        else:
            exc_message = message
        
        self.message = exc_message
        Logger.info(exc_message)