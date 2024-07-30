

from typing import Any, Dict, List, Literal, Optional

from typing_extensions import TypedDict

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.document.document_dto import DocumentFullDTO
from gws_core.experiment.experiment_dto import ExperimentDTO
from gws_core.lab.lab_config_dto import LabConfigModelDTO
from gws_core.protocol.protocol_dto import ExperimentProtocolDTO
from gws_core.resource.view.view_dto import CallViewResultDTO
from gws_core.user.activity.activity_dto import ActivityDTO


class LabStartDTO(BaseModelDTO):
    lab_config: LabConfigModelDTO


class SaveExperimentToSpaceDTO(BaseModelDTO):
    experiment: ExperimentDTO
    protocol: ExperimentProtocolDTO
    lab_config: LabConfigModelDTO


class SaveReportToSpaceDTO(BaseModelDTO):
    report: DocumentFullDTO
    experiment_ids: List[str]
    lab_config: LabConfigModelDTO
    resource_views: Dict[str, CallViewResultDTO]


class SpaceSendMailDTO(BaseModelDTO):
    receiver_ids: List[str]
    mail_template: Literal['experiment-finished', 'generic']
    data: Optional[Any]
    subject: Optional[str]  # if provided, it override the template subject


class SendExperimentFinishMailData(BaseModelDTO):
    """Experiment info when send finish mail
    """
    title: str
    status: str
    experiment_link: str


class LabActivityReponseDTO(BaseModelDTO):
    running_experiments: int
    queued_experiments: int
    last_activity: Optional[ActivityDTO]
    dev_env_running: bool


class SpaceReportRichTextFileViewData(TypedDict):
    """Object representing a file view in a rich text for a report transfered to space """
    id: str
    title: Optional[str]
    caption: Optional[str]
