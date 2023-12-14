# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from datetime import datetime
from typing import List, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.logger import MessageType


class LogDTO(BaseModelDTO):
    level: MessageType
    date_time: datetime
    message: Optional[str]
    experiment_id: Optional[str]


class LogInfo(BaseModelDTO):
    name: str
    file_size: int


class LogsStatusDTO(BaseModelDTO):
    log_folder: str
    log_files: List[LogInfo]


class LogCompleteInfoDTO(BaseModelDTO):
    log_info: LogInfo
    content: str


class LogsBetweenDatesDTO(BaseModelDTO):
    logs: List[LogDTO]
    from_date: datetime
    to_date: datetime
    from_experiment_id: Optional[str]
    is_last_page: bool
