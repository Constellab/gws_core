

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from typing_extensions import TypedDict

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.lab.lab_config_dto import LabConfigModelDTO
from gws_core.model.typing_style import TypingStyle
from gws_core.note.note_dto import NoteFullDTO
from gws_core.protocol.protocol_dto import ScenarioProtocolDTO
from gws_core.resource.view.view_dto import CallViewResultDTO
from gws_core.scenario.scenario_dto import ScenarioDTO
from gws_core.user.activity.activity_dto import ActivityDTO


class LabStartDTO(BaseModelDTO):
    lab_config: LabConfigModelDTO


class SaveScenarioToSpaceDTO(BaseModelDTO):
    scenario: ScenarioDTO
    protocol: ScenarioProtocolDTO
    lab_config: LabConfigModelDTO


class SaveNoteToSpaceDTO(BaseModelDTO):
    note: NoteFullDTO
    scenario_ids: List[str]
    lab_config: LabConfigModelDTO
    resource_views: Dict[str, CallViewResultDTO]


class SpaceSendMailToUsersDTO(BaseModelDTO):
    receiver_ids: List[str]
    mail_template: Literal['scenario-finished', 'generic']
    data: Optional[Any]
    subject: Optional[str]  # if provided, it override the template subject


class SpaceSendMailToMailsDTO(BaseModelDTO):
    receiver_mails: List[str]
    mail_template: Literal['scenario-finished', 'generic']
    data: Optional[Any]
    subject: Optional[str]  # if provided, it override the template subject


class SpaceSendNotificationDTO(BaseModelDTO):
    """DTO to send a notification to users in a space
    """
    # List of user IDs to receive the notification
    # The user must be in the space of the current lab
    receiver_ids: List[str]
    text: str  # Main text of the notification
    # Link to the object related to the notification
    # can be a space route (starting with /app) or an URL
    link: Optional[str] = None
    # IDs of associated objects related to the notification (like scenarios, notes, etc.)
    associated_object_ids: Optional[List[str]] = None


class SendScenarioFinishMailData(BaseModelDTO):
    """Scenario info when send finish mail
    """
    title: str
    status: str
    scenario_link: str


class LabActivityReponseDTO(BaseModelDTO):
    running_scenarios: int
    queued_scenarios: int
    last_activity: Optional[ActivityDTO]
    dev_env_running: bool


class SpaceNoteRichTextFileViewData(TypedDict):
    """Object representing a file view in a rich text for a note transfered to space """
    id: str
    title: Optional[str]
    caption: Optional[str]


class ShareResourceWithSpaceDTO(BaseModelDTO):
    resource_id: str
    name: str
    typing_name: str
    style: TypingStyle
    token: str
    valid_until: Optional[datetime] = None


class SpaceSyncObjectDTO(BaseModelDTO):
    """Object representing a space sync object
    """
    id: str
    folder_id: str
    last_sync_at: datetime
    last_sync_by_id: str


class SpaceDocumentDTO(BaseModelDTO):
    """Object representing a space document
    """
    id: str
    name: str
    size: int
    mimeType: str
    type: Literal['UPLOADED_DOCUMENT', 'CONSTELLAB_DOCUMENT']


class SpaceHierarchyObjectType(Enum):
    """Enum representing the type of a space hierarchy object
    """
    FOLDER = 'FOLDER'
    DOCUMENT = 'DOCUMENT'
    CONSTELLAB_DOCUMENT = 'CONSTELLAB_DOCUMENT'
    NOTE = 'NOTE'
    SCENARIO = 'SCENARIO'
    RESOURCE = 'RESOURCE'


class SpaceHierarchyObjectDTO(BaseModelDTO):
    """Object representing a space hierarchy object
    """
    id: str
    name: str
    objectType: SpaceHierarchyObjectType
    parentId: Optional[str] = None


class SpaceRootFolderUserRole(Enum):
    OWNER = 'OWNER'
    USER = 'USER'
    VIEWER = 'VIEWER'
