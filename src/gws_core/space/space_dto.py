from datetime import datetime
from enum import Enum
from typing import Any, Literal, Union

from pydantic import field_validator
from typing_extensions import TypedDict

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.lab.lab_config_dto import LabConfigModelDTO
from gws_core.model.typing_style import TypingStyle
from gws_core.note.note_dto import NoteFullDTO
from gws_core.protocol.protocol_dto import ScenarioProtocolDTO
from gws_core.scenario.scenario_dto import ScenarioDTO
from gws_core.user.activity.activity_dto import ActivityDTO
from gws_core.user.user_dto import UserDTO


class LabStartDTO(BaseModelDTO):
    lab_config: LabConfigModelDTO


class SaveScenarioToSpaceDTO(BaseModelDTO):
    scenario: ScenarioDTO
    protocol: ScenarioProtocolDTO
    lab_config: LabConfigModelDTO


class SaveNoteToSpaceDTO(BaseModelDTO):
    note: NoteFullDTO
    scenario_ids: list[str]
    lab_config: LabConfigModelDTO


class SpaceSendMailToUsersDTO(BaseModelDTO):
    receiver_ids: list[str]
    mail_template: Literal["scenario-finished", "generic"]
    data: Any | None
    subject: str | None  # if provided, it override the template subject


class SpaceSendMailToMailsDTO(BaseModelDTO):
    receiver_mails: list[str]
    mail_template: Literal["scenario-finished", "generic"]
    data: Any | None
    subject: str | None  # if provided, it override the template subject


class SpaceSendNotificationDTO(BaseModelDTO):
    """DTO to send a notification to users in a space"""

    # List of user IDs to receive the notification
    # The user must be in the space of the current lab
    receiver_ids: list[str]
    text: str  # Main text of the notification
    # Link to the object related to the notification
    # can be a space route (starting with /app) or an URL
    link: str | None = None
    # IDs of associated objects related to the notification (like scenarios, notes, etc.)
    associated_object_ids: list[str] | None = None


class SendScenarioFinishMailData(BaseModelDTO):
    """Scenario info when send finish mail"""

    title: str
    status: str
    scenario_link: str


class LabActivityReponseDTO(BaseModelDTO):
    running_scenarios: int
    queued_scenarios: int
    last_activity: ActivityDTO | None
    dev_env_running: bool


class SpaceNoteRichTextFileViewData(TypedDict):
    """Object representing a file view in a rich text for a note transfered to space"""

    id: str
    title: str | None
    caption: str | None


class ShareResourceWithSpaceDTO(BaseModelDTO):
    resource_id: str
    name: str
    typing_name: str
    style: TypingStyle
    token: str
    valid_until: datetime | None = None
    is_application: bool


class SpaceSyncObjectDTO(BaseModelDTO):
    """Object representing a space sync object"""

    id: str
    folder_id: str
    last_sync_at: datetime
    last_sync_by_id: str


class SpaceDocumentDTO(BaseModelDTO):
    """Object representing a space document"""

    id: str
    name: str
    size: int
    mimeType: str
    type: Literal["UPLOADED_DOCUMENT", "CONSTELLAB_DOCUMENT"]


SpaceHierarchyObjectType = Union[
    Literal[
        "FOLDER", "DOCUMENT", "CONSTELLAB_DOCUMENT", "NOTE", "SCENARIO", "RESOURCE", "APPLICATION"
    ],
    str,  # Allow any string value,if a new type is added in space
]


class SpaceHierarchyObjectDTO(BaseModelDTO):
    """Object representing a space hierarchy object"""

    id: str
    name: str
    objectType: SpaceHierarchyObjectType
    parentId: str | None = None


class SpaceGroupType(str, Enum):
    SINGLE_USER = "SINGLE_USER"
    TEAM = "TEAM"


class SpaceGroupDTO(BaseModelDTO):
    id: str
    label: str
    type: SpaceGroupType
    user: UserDTO | None = None

    @field_validator("user", mode="before")
    @classmethod
    def convert_user(cls, v):
        return UserDTO.from_user_space(v)


class SpaceGroupListDTO(BaseModelDTO):
    groups: list[SpaceGroupDTO]


class DocumentUploadOverrideMode(str, Enum):
    """Enum representing how to handle existing files with the same name when uploading documents"""

    IGNORE = "IGNORE"  # ignore the new document if it already exists
    ERROR = "ERROR"  # throw an error if the document already exists
    REPLACE = "REPLACE"  # replace the existing document with the new one
    RENAME = "RENAME"  # rename the new document with '_1' if it already exists
