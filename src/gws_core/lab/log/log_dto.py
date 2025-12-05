from datetime import datetime

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.core.utils.logger import LogContext, MessageType


class LogDTO(BaseModelDTO):
    level: MessageType
    date_time: datetime
    message: str | None
    context: LogContext
    context_id: str | None = None
    stack_trace: str | None = None


class LogInfo(BaseModelDTO):
    name: str
    file_size: int


class LogsStatusDTO(BaseModelDTO):
    log_folder: str
    log_files: list[LogInfo]


class LogCompleteInfoDTO(BaseModelDTO):
    log_info: LogInfo
    content: list[LogDTO]


class LogsBetweenDatesDTO(BaseModelDTO):
    logs: list[LogDTO]
    from_date: datetime
    to_date: datetime
    context: LogContext | None = None
    context_id: str | None = None
    is_last_page: bool
