

from datetime import datetime
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
