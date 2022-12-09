# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from enum import Enum
from typing import List, TypedDict, final

from fastapi.encoders import jsonable_encoder
from peewee import CharField, FloatField
from starlette_context import context

from gws_core.core.model.db_field import DateTimeUTC
from gws_core.core.utils.date_helper import DateHelper

from ..core.decorator.json_ignore import json_ignore
from ..core.exception.exceptions import BadRequestException
from ..core.model.model import Model
from ..core.utils.http_helper import HTTPHelper
from ..core.utils.logger import Logger


class ProgressBarMessageType(str, Enum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    PROGRESS = "PROGRESS"


class ProgressBarMessageWithType(TypedDict):
    type: ProgressBarMessageType
    message: str
    progress: float


class ProgressBarMessage(TypedDict):
    type: ProgressBarMessageType
    text: str
    datetime: str


@final
@json_ignore(['process_id', 'process_typing_name'])
class ProgressBar(Model):
    """
    ProgressBar class
    """

    process_id = CharField(null=True, index=True)
    process_typing_name = CharField(null=True)

    current_value = FloatField(default=0.0)
    started_at = DateTimeUTC(null=True)
    ended_at = DateTimeUTC(null=True)

    _MAX_VALUE = 100.0
    _MIN_VALUE = 0.0

    _table_name = "gws_process_progress_bar"
    _max_message_stack_length = 64

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.is_saved():
            self._init_data()

    @property
    def is_initialized(self):
        return self.started_at is not None

    @property
    def is_running(self):
        return self.is_initialized and self.ended_at is None

    @property
    def is_finished(self):
        return self.is_initialized and self.ended_at is not None

    def _init_data(self) -> None:
        self.data = {
            "messages": [],
        }
        self.started_at = None
        self.ended_at = None

    def reset(self) -> 'ProgressBar':
        """
        Reset the progress bar

        :return: Returns True if is progress bar is successfully reset;  False otherwise
        :rtype: `bool`
        """
        self._init_data()

        return self.save()

    ################################################## MESSAGE #################################################

    def add_info_message(self, message: str):
        self.add_message(message, ProgressBarMessageType.INFO)

    def add_success_message(self, message: str):
        self.add_message(message, ProgressBarMessageType.SUCCESS)

    def add_error_message(self, message: str):
        self.add_message(message, ProgressBarMessageType.ERROR)

    def add_warning_message(self, message: str):
        self.add_message(message, ProgressBarMessageType.WARNING)

    def add_message(self, message: str, type_: ProgressBarMessageType = ProgressBarMessageType.INFO):
        self._add_message(message, type_)

        self.save()

    def add_messages(self, messages: List[ProgressBarMessageWithType]) -> None:

        for message in messages:
            if message["type"] == ProgressBarMessageType.PROGRESS:
                self._update_progress(value=message["progress"], message=message["message"])
            else:
                self._add_message(message["message"], message["type"])

        # save only once at the end
        self.save()

    def _add_message(self, message: str, type_: ProgressBarMessageType = ProgressBarMessageType.INFO):
        dtime = jsonable_encoder(DateHelper.now_utc())

        progress_bar_message: ProgressBarMessage = {
            "type": type_,
            "text": message,
            "datetime": dtime
        }
        self.data["messages"].append(progress_bar_message)
        if len(self.data["messages"]) > self._max_message_stack_length:
            self.data["messages"].pop(0)
        self._log_message(message, type_)

    def start(self):
        if self.is_initialized:
            raise BadRequestException("The progress bar has already started")

        self.started_at = DateHelper.now_utc()
        self.save()

    def stop_success(self, success_message: str) -> None:
        self._stop()
        self.add_success_message(success_message)

    def stop_error(self, error_message: str) -> None:
        self._stop()
        self.add_error_message(error_message)

    def stop(self) -> None:
        self._stop()
        self.save()

    def _stop(self) -> None:
        self.current_value = self._MAX_VALUE
        self.ended_at = DateHelper.now_utc()

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
            #perc = value/self.get_max_value()
            perc = value
            self._add_message("{:1.1f}%: {}".format(perc, message), ProgressBarMessageType.PROGRESS)

    @property
    def messages(self) -> List[ProgressBarMessage]:
        return self.data["messages"]

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

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns JSON string or dictionnary representation of the model.

        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """

        _json = super().to_json(deep=deep, **kwargs)

        _json["process"] = {
            "id": self.process_id,
            "typing_name": self.process_typing_name,
        }

        _json["messages"] = self.messages

        return _json

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        return {}
    ################################################## CLASS METHODS #################################################

    @classmethod
    def add_message_to_current(cls, message: str, type_: ProgressBarMessageType = ProgressBarMessageType.INFO) -> None:
        progress_bar: ProgressBar = cls.get_current_progress_bar()

        if progress_bar is None:
            cls._log_message(message, type_)
            return

        progress_bar.add_message(message=message, type_=type_)

    @classmethod
    def _log_message(cls, message: str, type_: ProgressBarMessageType) -> None:
        if type_ == ProgressBarMessageType.INFO or type_ == ProgressBarMessageType.SUCCESS:
            Logger.info(message)
        elif type_ == ProgressBarMessageType.ERROR:
            Logger.error(message)
        elif type_ == ProgressBarMessageType.WARNING:
            Logger.warning(message)
        elif type_ == ProgressBarMessageType.PROGRESS:
            Logger.progress(message)

    @classmethod
    def get_by_process_id(cls, process_id: str) -> 'ProgressBar':
        return ProgressBar.get(ProgressBar.process_id == process_id)

    @classmethod
    def get_current_progress_bar(cls) -> 'ProgressBar':
        """
        Get the current progress bar.

        This method allow accessing the current progress everywhere (i.e. at the application level)
        """
        if not HTTPHelper.is_http_context():
            return None
        return context.data.get("progress_bar")

    class Meta:
        indexes = (
            # create a unique on process_id, process_typing_name
            (('process_id', 'process_typing_name'), True),
        )
