# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from enum import Enum, unique


class GWSException(Enum):
    INTERNAL_SERVER_ERROR = "Internal server error"
    WRONG_CREDENTIALS = "Could not validate credentials"
    WRONG_CREDENTIALS_INVALID_API_KEY = "Not authorized. Invalid API key"
    WRONG_CREDENTIALS_USER_NOT_FOUND = "Not authorized. Cannot generate user access token. User not found"
    WRONG_CREDENTIALS_USER_NOT_ACTIVATED = "Not authorized. Cannot generate user access token. User not active",
    INVALID_TOKEN = "Not authorized. Invalid token",
