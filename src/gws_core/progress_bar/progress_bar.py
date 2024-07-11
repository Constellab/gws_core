

from datetime import datetime
from typing import Any, Dict, List, Optional, final

from fastapi.encoders import jsonable_encoder
from peewee import CharField, FloatField

from gws_core.core.classes.observer.message_level import MessageLevel
from gws_core.core.model.db_field import DateTimeUTC, JSONField
from gws_core.core.utils.date_helper import DateHelper
from gws_core.progress_bar.progress_bar_dto import (
    ProgressBarConfigDTO, ProgressBarDTO, ProgressBarMessageDTO,
    ProgressBarMessageWithTypeDTO)

from ..core.exception.exceptions import BadRequestException
from ..core.model.model import Model


@final
class ProgressBar(Model):
    """
    ProgressBar class
    """

    process_id = CharField(null=False, index=True, unique=True)
    process_typing_name = CharField(null=False)

    current_value = FloatField(default=0.0)
    started_at = DateTimeUTC(null=True)
    ended_at = DateTimeUTC(null=True)

    elapsed_time = FloatField(null=True)
    second_start = DateTimeUTC(null=True)

    data: Dict[str, Any] = JSONField(null=True)

    _MAX_VALUE = 100.0
    _MIN_VALUE = 0.0
    _MAX_MESSAGE_LENGTH = 10000

    _table_name = "gws_process_progress_bar"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.is_saved():
            self._init_data()

    @property
    def is_started(self):
        return self.started_at is not None

    @property
    def is_running(self):
        return self.is_started and self.ended_at is None

    @property
    def is_finished(self):
        return self.is_started and self.ended_at is not None

    def _init_data(self) -> None:
        self.data = {
            "messages": [],
        }
        self.started_at = None
        self.ended_at = None
        self.elapsed_time = None
        self.second_start = None
        self.current_value = self._MIN_VALUE

    def reset(self) -> 'ProgressBar':
        """
        Reset the progress bar

        :return: Returns True if is progress bar is successfully reset;  False otherwise
        :rtype: `bool`
        """
        self._init_data()

        return self.save()

    def get_elapsed_time(self) -> float:
        """
        Calculate the elapsed time in milliseconds

        :return: Returns the elapsed time in milliseconds
        :rtype: `float`
        """
        # if the second start is currently running
        if self.second_start is not None and self.ended_at is None:
            return (DateHelper.now_utc() - self.second_start).total_seconds() * 1000

        if self.elapsed_time is not None:
            return self.elapsed_time

        if self.started_at is None:
            return 0.0

        if self.ended_at is None:
            return (DateHelper.now_utc() - self.started_at).total_seconds() * 1000

        return (self.ended_at - self.started_at).total_seconds() * 1000

    def get_last_execution_time(self) -> float:
        """
        Must be called only when the progress bar is finished
        Get the last execution time. If no second start, return the execution duration, else return the second start duration

        :return: Returns the last execution time in milliseconds
        :rtype: `datetime`
        """
        if self.ended_at is None:
            return 0

        if self.second_start is not None:
            return (self.ended_at - self.second_start).total_seconds() * 1000

        return (self.ended_at - self.started_at).total_seconds() * 1000

    ################################################## MESSAGE #################################################

    def add_debug_message(self, message: str):
        self.add_message(message, MessageLevel.DEBUG)

    def add_info_message(self, message: str):
        self.add_message(message, MessageLevel.INFO)

    def add_success_message(self, message: str):
        self.add_message(message, MessageLevel.SUCCESS)

    def add_error_message(self, message: str):
        self.add_message(message, MessageLevel.ERROR)

    def add_warning_message(self, message: str):
        self.add_message(message, MessageLevel.WARNING)

    def add_message(self, message: str, type_: MessageLevel = MessageLevel.INFO):
        self._add_message(message, type_)

        self.save()

    def add_messages(self, messages: List[ProgressBarMessageWithTypeDTO]) -> None:

        for message in messages:

            message_content = self._check_message_length(message.message)

            if message.type == MessageLevel.PROGRESS:
                self._update_progress(
                    value=message.progress, message=message_content)
            else:
                self._add_message(message_content, message.type)

        # save only once at the end
        self.save()

    def _check_message_length(self, message: str) -> str:
        if len(message) > self._MAX_MESSAGE_LENGTH:
            info_message = f"[INFO] Message too long, it is truncated to {self._MAX_MESSAGE_LENGTH} characters. Check the server logs for the full message."
            return f"{info_message}\n{message[:self._MAX_MESSAGE_LENGTH]}\n{info_message}"

        return message

    def _add_message(self, message: str, type_: MessageLevel = MessageLevel.INFO):
        dtime = jsonable_encoder(DateHelper.now_utc())

        progress_bar_message = ProgressBarMessageDTO(
            type=type_,
            text=message,
            datetime=dtime
        )
        self.data["messages"].append(progress_bar_message.to_json_dict())

    def start(self):
        if self.is_started:
            raise BadRequestException("The progress bar has already started")

        self.started_at = DateHelper.now_utc()
        self.current_value = self._MIN_VALUE
        self.save()

    def trigger_second_start(self):
        self.second_start = DateHelper.now_utc()
        self.ended_at = None
        self.save()

    def stop_success(self, success_message: str, elapsed_time: float) -> None:
        self._stop(elapsed_time)
        self.add_success_message(success_message)

    def stop_error(self, error_message: str, elapsed_time: float) -> None:
        self._stop(elapsed_time)
        self.add_error_message(error_message)

    def _stop(self, elapsed_time: float) -> None:
        self.current_value = self._MAX_VALUE
        self.ended_at = DateHelper.now_utc()
        self.elapsed_time = elapsed_time

    def update_progress(self, value: float, message: str) -> None:
        """
        Increment the progress-bar value and log a progress message
        """
        self._update_progress(value, message)
        self.save()

    def _update_progress(self, value: float, message: str) -> None:
        """
        Increment the progress-bar value and log a progress message
        """

        # check if we update the progres
        value = self._update_progress_value(value)
        if message:
            # perc = value/self.get_max_value()
            perc = value
            self._add_message("{:1.1f}%: {}".format(
                perc, message), MessageLevel.PROGRESS)

    def get_messages(self) -> List[ProgressBarMessageDTO]:
        return ProgressBarMessageDTO.from_json_list(self.data["messages"])

    def get_last_message(self) -> Optional[ProgressBarMessageDTO]:
        messages = self.get_messages()
        if not messages:
            return None
        return messages[-1]

    def get_messages_paginated(self, nb_of_messages: int, before_date: datetime = None) -> List[ProgressBarMessageDTO]:
        """
        Get the last nb_of_messages messages
        :param nb_of_messages: number of messages to get
        :param from_datatime: if provided, get the last nb_of_messages messages before this date
        :return:
        """
        messages = self.get_messages()
        if not messages:
            return []

        # get a copy of the message
        messages = [*messages]
        messages.reverse()

        if before_date is None:
            return messages[:nb_of_messages]

        filtered_messages = []
        for message in messages:
            if DateHelper.from_iso_str(message.datetime) < before_date:
                filtered_messages.append(message)

            if len(filtered_messages) >= nb_of_messages:
                break

        return filtered_messages

    def get_messages_as_str(self) -> str:
        return "\n".join([str(message) for message in self.get_messages()])

    ################################################## VALUE #################################################

    def _update_progress_value(self, value: float) -> float:
        if value < self._MIN_VALUE:
            value = self._MIN_VALUE

        if value > self._MAX_VALUE:
            value = self._MAX_VALUE

        self.current_value = value
        return value

    def get_total_duration(self) -> float:
        if self.started_at is None or self.ended_at is None:
            return 0.0
        return (self.ended_at - self.started_at).total_seconds()

    ################################################## TO JSON #################################################

    def to_dto(self) -> ProgressBarDTO:
        return ProgressBarDTO(
            id=self.id,
            started_at=self.started_at,
            ended_at=self.ended_at,
            current_value=self.current_value,
            elapsed_time=self.get_elapsed_time(),
            second_start=self.second_start,
        )

    def to_config_dto(self) -> ProgressBarConfigDTO:
        return ProgressBarConfigDTO(
            started_at=self.started_at,
            ended_at=self.ended_at,
            current_value=self.current_value,
            elapsed_time=self.get_elapsed_time(),
            second_start=self.second_start,
        )

    @classmethod
    def from_config_dto(cls, dto: ProgressBarConfigDTO) -> 'ProgressBar':
        progress_bar = ProgressBar()
        progress_bar.started_at = dto.started_at
        progress_bar.ended_at = dto.ended_at
        progress_bar.current_value = dto.current_value
        progress_bar.elapsed_time = dto.elapsed_time
        progress_bar.second_start = dto.second_start
        return progress_bar
