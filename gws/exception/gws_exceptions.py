from enum import Enum, unique


@unique
class GWSException(Enum):
    INTERNAL_SERVER_ERROR = "Internal server error"
    WRONG_CREDENTIALS = "Could not validate credentials"
