# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Any, List, Literal, Optional, TypedDict

from gws_core.lab.lab_config_model import LabConfig


class LabStartDTO(TypedDict):
    lab_config: LabConfig


class SaveExperimentToCentralDTO(TypedDict):
    experiment: dict
    protocol: dict
    lab_config: dict


class CentralSendMailDTO(TypedDict):
    receiver_ids: List[str]
    mail_template: Literal['experiment-finished']
    data: Optional[Any]


class SendExperimentFinishMailData(TypedDict):
    """Experiment info when send finish mail
    """
    title: str
    status: str
    experiment_link: str