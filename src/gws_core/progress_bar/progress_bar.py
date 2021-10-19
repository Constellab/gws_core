# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import time
from datetime import datetime
from typing import final

from fastapi.encoders import jsonable_encoder
from peewee import CharField
from starlette_context import context

from ..core.decorator.json_ignore import json_ignore
from ..core.exception.exceptions import BadRequestException
from ..core.model.model import Model
from ..core.utils.http_helper import HTTPHelper
from ..core.utils.logger import Logger
from ..model.typing_register_decorator import typing_registrator


@final
@json_ignore(['process_uri', 'process_typing_name'])
@typing_registrator(unique_name="ProgressBar", object_type="MODEL", hide=True)
class ProgressBar(Model):
    """
    ProgressBar class
    """

    process_uri = CharField(null=True, index=True)
    process_typing_name = CharField(null=True)

    _min_allowed_delta_time = 1.0
    _min_value = 0.0

    _is_removable = False
    _table_name = "gws_process_progress_bar"
    _max_message_stack_length = 64

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.id:
            self._init_data()

    # -- A --
    @classmethod
    def add_message_to_current(cls, message: str) -> None:
        progress_bar: ProgressBar = cls.get_current_progress_bar()

        if progress_bar is None:
            Logger.progress(message=message)
            return

        progress_bar.add_message(message=message)

    def add_message(self, message: str):
        dtime = jsonable_encoder(datetime.now())
        self.data["messages"].append({
            "text": message,
            "datetime": dtime
        })

        if len(self.data["messages"]) > self._max_message_stack_length:
            self.data["messages"].pop(0)

        Logger.progress(message)

    # -- C --

    def _compute_remaining_seconds(self):
        nb_remaining_steps = self.data["max_value"] - self.data["value"]
        if self.data["average_speed"] > 0.0:
            nb_remaining_seconds = nb_remaining_steps / \
                self.data["average_speed"]
            return nb_remaining_seconds
        else:
            return -1

    # -- G --

    @classmethod
    def get_current_progress_bar(cls) -> 'ProgressBar':
        """
        Get the current progress bar.

        This method allow accessing the current progress everywhere (i.e. at the application level)
        """
        if not HTTPHelper.is_http_context():
            return None
        return context.data.get("progress_bar")

    def get_max_value(self) -> float:
        return self.data["max_value"]

    # -- I --

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

    # -- R --

    def _init_data(self) -> None:
        self.data = {
            "value": 0.0,
            "max_value": 0.0,
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

    # -- S --

    def start(self, max_value: float = 100.0):
        if max_value <= 0.0:
            raise BadRequestException("Invalid max value")

        if self.data["start_time"] > 0.0:
            raise BadRequestException("The progress bar has already started")

        self.data["max_value"] = max_value
        self.data["start_time"] = time.perf_counter()
        self.data["current_time"] = self.data["start_time"]
        self.save()

    def stop(self, message: str):
        _max = self.data["max_value"]

        if self.data["value"] < _max:
            self.set_value(_max, message)

        self.data["remaining_time"] = 0.0
        self.save()

    def set_value(self, value: float, message: str):
        """
        Increment the progress-bar value
        """

        if value == self._min_value:
            value = self._min_value + 1e-6

        _max = self.data["max_value"]
        if _max == 0.0:
            self.start()
            #raise BadRequestException("The progress bar has not started")

        # if value >= _max:
        #     value = _max - 1  # prevent blocking the progress_bar

        if value < self._min_value:
            value = self._min_value

        current_time = time.perf_counter()
        delta_time = current_time - self.data["current_time"]
        ignore_update = delta_time < self._min_allowed_delta_time and value < _max
        if ignore_update:
            return

        self.data["value"] = value
        self.data["current_time"] = current_time
        self.data["elapsed_time"] = current_time - self.data["start_time"]
        self.data["average_speed"] = self.data["value"] / \
            self.data["elapsed_time"]
        self.data["remaining_time"] = self._compute_remaining_seconds()

        if message:
            perc = value/self.data["max_value"]
            self.add_message("{:.1%}: {}".format(perc, message))

        self.save()

    def set_max_value(self, value: int):
        _max = self.data["max_value"]

        if self.data["value"] > 0:
            raise BadRequestException("The progress bar has already started")

        if isinstance(_max, int):
            raise BadRequestException("The max value must be an integer")

        if _max <= 0:
            raise BadRequestException(
                "The max value must be greater than zero")

        self.data["max_value"] = value
        self.save()

    @classmethod
    def get_by_process_uri(cls, process_uri: str) -> 'ProgressBar':
        return ProgressBar.get(ProgressBar.process_uri == process_uri)

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

    class Meta:
        indexes = (
            # create a unique on process_uri, process_typing_name
            (('process_uri', 'process_typing_name'), True),
        )
