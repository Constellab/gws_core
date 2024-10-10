
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
    RUN_SCENARIO = "RUN_SCENARIO"
    DELETE_SCENARIO_INTERMEDIATE_RESOURCES = "DELETE_SCENARIO_INTERMEDIATE_RESOURCES"
    RUN_PROCESS = "RUN_PROCESS"
    STOP_SCENARIO = "STOP_SCENARIO"
    LAB_START = "LAB_START"


class ActivityObjectType(Enum):
    SCENARIO = "SCENARIO"
    PROCESS = "PROCESS"
    USER = "USER"
    NOTE = "NOTE"
    NOTE_TEMPLATE = "NOTE_TEMPLATE"


class ActivityDTO(ModelDTO):
    user: UserDTO
    activity_type: ActivityType
    object_type: ActivityObjectType
    object_id: str
