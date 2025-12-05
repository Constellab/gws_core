from datetime import datetime

from gws_core.core.classes.observer.message_level import MessageLevel
from gws_core.core.model.model_dto import BaseModelDTO


class ProgressBarMessageWithTypeDTO(BaseModelDTO):
    type: MessageLevel
    message: str
    progress: float | None


class ProgressBarMessageDTO(BaseModelDTO):
    type: MessageLevel
    text: str
    datetime: str
    progress: float | None = None

    def __str__(self) -> str:
        return f"{self.type} - {self.datetime} - {self.text}"

    def is_after(self, other: "ProgressBarMessageDTO") -> bool:
        return self.get_datetime() > other.get_datetime()

    def get_datetime(self):
        return datetime.fromisoformat(self.datetime)


class ProgressBarConfigDTO(BaseModelDTO):
    started_at: datetime | None
    ended_at: datetime | None
    current_value: float
    elapsed_time: float
    second_start: datetime | None


class ProgressBarDTO(ProgressBarConfigDTO):
    id: str


class ProgressBarMessagesBetweenDatesDTO(BaseModelDTO):
    from_datatime: datetime | None
    to_datatime: datetime | None
    messages: list[ProgressBarMessageDTO]
