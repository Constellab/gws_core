
from enum import Enum

from gws_core.core.model.model_dto import ModelDTO
from gws_core.user.user_dto import UserDTO


class ActivityType(Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    ARCHIVE = "ARCHIVE"
    UNARCHIVE = "UNARCHIVE"
    VALIDATE = "VALIDATE"
    HTTP_AUTHENTICATION = "HTTP_AUTHENTICATION"
    RUN_EXPERIMENT = "RUN_EXPERIMENT"
    RUN_PROCESS = "RUN_PROCESS"
    STOP_EXPERIMENT = "STOP_EXPERIMENT"
    LAB_START = "LAB_START"


class ActivityObjectType(Enum):
    EXPERIMENT = "EXPERIMENT"
    PROCESS = "PROCESS"
    USER = "USER"
    REPORT = "REPORT"
    REPORT_TEMPLATE = "REPORT_TEMPLATE"


class ActivityDTO(ModelDTO):
    user: UserDTO
    activity_type: ActivityType
    object_type: ActivityObjectType
    object_id: str
