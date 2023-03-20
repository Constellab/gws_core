# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, List, Literal, Optional

from gws_core.lab.lab_config_model import LabConfig
from typing_extensions import TypedDict


class LabStartDTO(TypedDict):
    lab_config: LabConfig


class SaveExperimentToSpaceDTO(TypedDict):
    experiment: dict
    protocol: dict
    lab_config: dict


class SaveReportToSpaceDTO(TypedDict):
    report: dict
    experiment_ids: List[str]
    lab_config: dict


class SpaceSendMailDTO(TypedDict):
    receiver_ids: List[str]
    mail_template: Literal['experiment-finished']
    data: Optional[Any]


class SendExperimentFinishMailData(TypedDict):
    """Experiment info when send finish mail
    """
    title: str
    status: str
    experiment_link: str
