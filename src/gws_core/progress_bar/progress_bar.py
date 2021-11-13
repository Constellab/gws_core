# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time
from datetime import datetime
from enum import Enum
from typing import List, final

from fastapi.encoders import jsonable_encoder
from peewee import CharField
from starlette_context import context

from ..core.decorator.json_ignore import json_ignore
from ..core.exception.exceptions import BadRequestException
from ..core.model.model import Model
from ..core.utils.http_helper import HTTPHelper
from ..core.utils.logger import Logger
from ..model.typing_register_decorator import typing_registrator


class ProgressBarMessageType(str, Enum):
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    PROGRESS = "PROGRESS"


@final
@json_ignore(['process_uri', 'process_typing_name'])
@typing_registrator(unique_name="ProgressBar", object_type="MODEL", hide=True)
class ProgressBar(Model):
    """
    ProgressBar class
    """

    process_uri = CharField(null=True, index=True)
    process_typing_name = CharField(null=True)

    _MIN_ALLOWED_DELTA_TIME = 1.0
    _MAX_VALUE = 100.0
    _MIN_VALUE = 0.0

    _is_removable = False
    _table_name = "gws_process_progress_bar"
    _max_message_stack_length = 64

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.id:
            self._init_data()

    @property
    def is_initialized(self):
        return self.data["max_value"] > 0.0

    @property
    def is_running(self):
        return self.is_initialized and \
            self.data["value"] > 0.0 and \
            self.data["value"] < self.data["max_value"]

    @property
    def is_finished(self):
        return self.is_initialized and \
            self.data["value"] >= self.data["max_value"]

    def _init_data(self) -> None:
        self.data = {
            "value": self._MIN_VALUE,
            "max_value": self._MAX_VALUE,
            "average_speed": 0.0,
            "start_time": 0.0,
            "current_time": 0.0,
            "elapsed_time": 0.0,
            "remaining_time": 0.0,
            "messages": [],
        }

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
        dtime = jsonable_encoder(datetime.now())
        self.data["messages"].append({
            "type": type_,
            "text": message,
            "datetime": dtime
        })
        if len(self.data["messages"]) > self._max_message_stack_length:
            self.data["messages"].pop(0)
        self._log_message(message, type_)
        self.save()

    def start(self, max_value: float = 100.0):
        if max_value <= 0.0:
            raise BadRequestException("Invalid max value")
        if self.data["start_time"] > 0.0:
            raise BadRequestException("The progress bar has already started")
        self.data["max_value"] = max_value
        self.data["start_time"] = time.perf_counter()
        self.data["current_time"] = self.data["start_time"]
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
        _max = self.data["max_value"]
        if self.data["value"] < _max:
            self._update_progress_value(_max)
        self.data["remaining_time"] = 0.0

    def update_progress(self, value: float, message: str) -> None:
        """
        Increment the progress-bar value and log a progress message
        """

        # check if we update the progres
        current_time = time.perf_counter()
        delta_time = current_time - self.data["current_time"]
        if delta_time < self._MIN_ALLOWED_DELTA_TIME and value < self.get_max_value():
            return
        value = self._update_progress_value(value)
        if message:
            #perc = value/self.get_max_value()
            perc = value
            self.add_message("{:1.1f}%: {}".format(perc, message), ProgressBarMessageType.PROGRESS)
        self.save()

    @property
    def messages(self) -> List[dict]:
        return self.data["messages"]

    ################################################## VALUE #################################################

    def get_max_value(self) -> float:
        return self.data["max_value"]

    def _update_progress_value(self, value: float) -> float:
        _max = self.data["max_value"]
        if _max == 0.0:
            self.start()
        #if value >= self._MAX_VALUE:
        #     value = self._MAX_VALUE - 1e-6  # prevent blocking the progress_bar
        if value < self._MIN_VALUE:
            value = self._MIN_VALUE
        current_time = time.perf_counter()
        self.data["value"] = value
        self.data["current_time"] = current_time
        self.data["elapsed_time"] = current_time - self.data["start_time"]
        self.data["average_speed"] = self.data["value"] / \
            self.data["elapsed_time"]
        self.data["remaining_time"] = self._compute_remaining_seconds()
        return value

    def _compute_remaining_seconds(self):
        nb_remaining_steps = self.data["max_value"] - self.data["value"]
        if self.data["average_speed"] > 0.0:
            nb_remaining_seconds = nb_remaining_steps / \
                self.data["average_speed"]
            return nb_remaining_seconds
        else:
            return -1

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
            "uri": self.process_uri,
            "typing_name": self.process_typing_name,
        }

        return _json

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
    def get_by_process_uri(cls, process_uri: str) -> 'ProgressBar':
        return ProgressBar.get(ProgressBar.process_uri == process_uri)

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
            # create a unique on process_uri, process_typing_name
            (('process_uri', 'process_typing_name'), True),
        )
