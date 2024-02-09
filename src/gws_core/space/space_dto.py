# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, Dict, List, Literal, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.experiment.experiment_dto import ExperimentDTO
from gws_core.lab.lab_config_dto import LabConfigModelDTO
from gws_core.protocol.protocol_dto import ExperimentProtocolDTO
from gws_core.report.report_dto import ReportFullDTO
from gws_core.resource.view.view_dto import CallViewResultDTO
from gws_core.user.activity.activity_dto import ActivityDTO


class LabStartDTO(BaseModelDTO):
    lab_config: LabConfigModelDTO


class SaveExperimentToSpaceDTO(BaseModelDTO):
    experiment: ExperimentDTO
    protocol: ExperimentProtocolDTO
    lab_config: LabConfigModelDTO


class SaveReportToSpaceDTO(BaseModelDTO):
    report: ReportFullDTO
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
