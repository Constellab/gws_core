

from datetime import datetime
from typing import List, Optional

from gws_core.core.classes.observer.message_level import MessageLevel
from gws_core.core.model.model_dto import BaseModelDTO


class ProgressBarMessageWithTypeDTO(BaseModelDTO):
    type: MessageLevel
    message: str
    progress: Optional[float]


class ProgressBarMessageDTO(BaseModelDTO):
    type: MessageLevel
    text: str
    datetime: str

    def __str__(self) -> str:
        return f"{self.type} - {self.datetime} - {self.text}"


class ProgressBarConfigDTO(BaseModelDTO):
    started_at: Optional[datetime]
    ended_at: Optional[datetime]
    current_value: float
    elapsed_time: float
    second_start: Optional[datetime]


class ProgressBarDTO(ProgressBarConfigDTO):
    id: str


class ProgressBarMessagesBetweenDatesDTO(BaseModelDTO):
    from_datatime: Optional[datetime]
    to_datatime: Optional[datetime]
    messages: List[ProgressBarMessageDTO]
