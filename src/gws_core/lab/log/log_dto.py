

from datetime import datetime
from typing import List, Optional

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.logger import LogContext, MessageType


class LogDTO(BaseModelDTO):
    level: MessageType
    date_time: datetime
    message: Optional[str]
    context: LogContext
    context_id: Optional[str] = None
    stack_trace: Optional[str] = None


class LogInfo(BaseModelDTO):
    name: str
    file_size: int


class LogsStatusDTO(BaseModelDTO):
    log_folder: str
    log_files: List[LogInfo]


class LogCompleteInfoDTO(BaseModelDTO):
    log_info: LogInfo
    content: List[LogDTO]


class LogsBetweenDatesDTO(BaseModelDTO):
    logs: List[LogDTO]
    from_date: datetime
    to_date: datetime
    from_scenario_id: Optional[str]
    is_last_page: bool
