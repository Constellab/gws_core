# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from enum import Enum
from typing import Any, Dict, Optional

from typing_extensions import TypedDict


class CredentialsType(Enum):
    """
    Different types of credentials
    """
    BASIC = "BASIC"
    S3 = "S3"
    OTHER = "OTHER"


class CredentialsDataBase(TypedDict):
    # this field contains meta info about the credentials
    __meta__: Dict[str, Any]


class CredentialsDataS3(CredentialsDataBase):
    """Format of the data for S3 credentials
    """
    endpoint_url: str
    region: str
    access_key_id: str
    secret_access_key: str
    bucket: Optional[str]


class CredentialsDataBasic(CredentialsDataBase):
    """Format of the data for Basic credentials
    """
    username: str
    password: str
    url: Optional[str]


# Format of the data for other credentials
# A simple string to string dictionary
CredentialsDataOther = Dict[str, str]
