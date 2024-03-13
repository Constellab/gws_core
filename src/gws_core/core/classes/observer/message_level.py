

from enum import Enum


class MessageLevel(str, Enum):
    """Level of messages for message dispatcher and progress bar
    """
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    PROGRESS = "PROGRESS"

    def get_int_value(self):
        values = {
            'DEBUG': 0,
            'INFO': 1,
            'SUCCESS': 2,
            'WARNING': 3,
            'ERROR': 4,
            'PROGRESS': 5,
        }
        return values[self.value]
