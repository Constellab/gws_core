from enum import Enum, unique


@unique
class GWSException(Enum):
    INTERNAL_SERVER_ERROR = "Internal server error"
    WRONG_CREDENTIALS = "Could not validate credentials"
    WRONG_CREDENTIALS_USER_NOT_FOUND = "Not authorized. Cannot generate user access token. User not found"
    WRONG_CREDENTIALS_USER_NOT_ACTIVATED = "Not authorized. Cannot generate user access token. User not active"
