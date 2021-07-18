# LICENSE
# This software is the exclusive property of Gencovery SAS. 
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import json
import time
from datetime import datetime
from peewee import  CharField
from fastapi.encoders import jsonable_encoder

from .db.model import Model
from .logger import Error, Info

class ProgressBar(Model):
    """
    ProgressBar class
    """

    process_uri = CharField(null=True, index=True)
    process_type = CharField(null=True)  #-> unique index (process_uri, process_type) is created in Meta
    
    _min_allowed_delta_time = 1.0
    _min_value = 0.0
    
    _is_removable = False
    _table_name = "gws_process_progress_bar"
    _max_message_stack_length = 64
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.id:
            self._reset()
    
    # -- A --
    
    def add_message(self, message="Experiment under progress ...", show_info=False):
        dtime = jsonable_encoder(datetime.now())
        self.data["messages"].append({
            "text": message,
            "datetime": dtime
        })
        
        if len(self.data["messages"]) > self._max_message_stack_length:
            self.data["messages"].pop(0)

        if show_info:
            Info(message)

    # -- C --
    
    def _compute_remaining_seconds(self):
        nb_remaining_steps = self.data["max_value"] - self.data["value"]
        if self.data["average_speed"] > 0.0:
            nb_remaining_seconds = nb_remaining_steps / self.data["average_speed"]
            return nb_remaining_seconds
        else:
            return -1
    
    # -- G --
    
    def get_max_value(self) -> float:
        return self.data["max_value"]
    
    # -- I --
    
    @property
    def is_initialized(self):
        return self.data["max_value"] > 0.0
    
    @property
    def is_running(self):
        return  self.is_initialized and \
                self.data["value"] > 0.0 and \
                self.data["value"] < self.data["max_value"]
    
    @property
    def is_finished(self):
        return  self.is_initialized and \
                self.data["value"] >= self.data["max_value"]
    
    # -- P --
    
    @property
    def process(self) -> 'Process':
        if not self.process_type:
            return None
        
        from .service.model_service import ModelService
        t = ModelService.get_model_type(self.process_type)
        return t.get(t.uri == self.process_uri)
    
    # -- R --

    def _reset(self) -> bool:
        """
        Reset the progress bar

        :return: Returns True if is progress bar is successfully reset;  False otherwise
        :rtype: `bool`
        """

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
        return self.save()

    # -- S --
    
    def start(self, max_value: float = 100.0):
        if max_value <= 0.0:
            raise Error("ProgressBar", "start", "Invalid max value")
    
        if self.data["start_time"] > 0.0:
            raise Error("ProgressBar", "start", "The progress bar has already started")
        
        self.data["max_value"] = max_value
        self.data["start_time"] = time.perf_counter()
        self.data["current_time"] = self.data["start_time"]
        self.add_message(message="Experiment started")
        self.save()
    
    def stop(self, message="End of experiment!"):
        _max = self.data["max_value"]
        
        if self.data["value"] < _max:
            self.set_value(_max, message)

        self.data["remaining_time"] = 0.0
        self.save()
        
    def set_value(self, value: float, message="Experiment under progress ...", show_info=False):
        """
        Increment the progress-bar value
        """
        
        if value == self._min_value:
            value = self._min_value + 1e-6

        _max = self.data["max_value"]        
        if _max == 0.0:
            self.start()
            #raise Error("ProgressBar", "start", "The progress bar has not started")
            
        if value > _max:
            value = _max
        
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
        self.data["average_speed"] = self.data["value"] / self.data["elapsed_time"]
        self.data["remaining_time"] = self._compute_remaining_seconds()
        self.add_message(message, show_info=show_info)
        
        if self.data["value"] == _max:
            self.stop()
        else:
            self.save()
        
    def set_max_value(self, value: int):
        _max = self.data["max_value"]
        
        if self.data["value"] > 0:
            raise Error("ProgressBar", "set_max_value", "The progress bar has already started")
        
        if isinstance(_max, int):
            raise Error("ProgressBar", "set_max_value", "The max value must be an integer")
       
        if _max <= 0:
            raise Error("ProgressBar", "set_max_value", "The max value must be greater than zero")
           
        self.data["max_value"] = value
        self.save()
    
    def to_json(self, *, shallow=False, stringify: bool=False, prettify: bool=False, **kwargs) -> (str, dict, ):
        """
        Returns JSON string or dictionnary representation of the model.
        
        :param stringify: If True, returns a JSON string. Returns a python dictionary otherwise. Defaults to False
        :type stringify: bool
        :param prettify: If True, indent the JSON string. Defaults to False.
        :type prettify: bool
        :return: The representation
        :rtype: dict, str
        """
        
        _json = super().to_json(**kwargs)
        
        bare = kwargs.get("bare")
        if bare:
            _json["process"] = {
                "uri": "",
                "type": "",
            }
            
            _json["data"] = {
                "value": 0.0,
                "max_value": 0.0,
                "average_speed": 0.0,
                "start_time": 0.0,
                "current_time": 0.0,
                "elapsed_time": 0.0,
                "remaining_time": 0.0,
                "messages": [],
            }
        else:
            _json["process"] = {
                "uri": _json["process_uri"],
                "type": _json["process_type"],
            }
        
        del _json["process_uri"]
        del _json["process_type"]
        
        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
        
        
    class Meta:
        indexes = (
            # create a unique on process_uri, process_type
            (('process_uri', 'process_type'), True),
        )
        