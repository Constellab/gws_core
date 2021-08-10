# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
import json
from typing import Any, Dict, Union

from ..model.typing import Typing


class ProcessType(Typing):
    """
    ProcessType class.
    """

    def to_json(self, *, stringify: bool = False, prettify: bool = False, **kwargs) -> Union[str, dict]:

        _json: Dict[str, Any] = super().to_json(**kwargs)

        # for compatibility
        _json["ptype"] = self.model_type

        model_t = self.get_model_type(self.model_type)
        specs = model_t.input_specs
        _json["input_specs"] = {}
        for name in specs:
            _json["input_specs"][name] = []
            t_list = specs[name]
            if not isinstance(t_list, tuple):
                t_list = (t_list, )

            for t in t_list:
                if t is None:
                    _json["input_specs"][name].append(None)
                else:
                    _json["input_specs"][name].append(t.full_classname())

        specs = model_t.output_specs
        _json["output_specs"] = {}
        for name in specs:
            _json["output_specs"][name] = []
            t_list = specs[name]
            if not isinstance(t_list, tuple):
                t_list = (t_list, )

            for t in t_list:
                if t is None:
                    _json["output_specs"][name].append(None)
                else:
                    _json["output_specs"][name].append(t.full_classname())

        _json["config_specs"] = model_t.config_specs
        for k in _json["config_specs"]:
            spec = _json["config_specs"][k]
            if "type" in spec and isinstance(spec["type"], type):
                t_str = spec["type"].__name__
                _json["config_specs"][k]["type"] = t_str

        _json["data"]["title"] = model_t.title
        _json["data"]["description"] = model_t.description
        _json["data"]["doc"] = inspect.getdoc(model_t)

        if stringify:
            if prettify:
                return json.dumps(_json, indent=4)
            else:
                return json.dumps(_json)
        else:
            return _json
