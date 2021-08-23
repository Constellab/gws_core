# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
from typing import Any, Dict, List, Type, final

from peewee import ModelSelect

from ..core.utils.utils import Utils
from ..model.typing import Typing, TypingObjectType
from ..process.process import Process
from ..resource.resource import Resource


@final
class ProcessType(Typing):
    """
    ProcessType class.
    """

    _object_type: TypingObjectType = "PROCESS"

    @classmethod
    def get_types(cls) -> ModelSelect:
        return cls.get_by_object_type(cls._object_type)

    def to_json(self, deep: bool = False, **kwargs) -> dict:

        _json: Dict[str, Any] = super().to_json(deep=deep, **kwargs)

        # for compatibility
        _json["ptype"] = self.model_type

        # retrieve the process python type
        model_t: Type[Process] = Utils.get_model_type(self.model_type)

        # Handle the resource input specs
        specs = model_t.input_specs
        _json["input_specs"] = {}
        for name in specs:
            _json["input_specs"][name] = []
            t_list: List[Type[Resource]] = specs[name]
            if not isinstance(t_list, tuple):
                t_list = (t_list, )

            for resource_type in t_list:
                if resource_type is None:
                    _json["input_specs"][name].append(None)
                else:
                    # set the resource typing name as input_spec
                    _json["input_specs"][name].append(
                        resource_type._typing_name)

        # Handle the resource output specs
        specs = model_t.output_specs
        _json["output_specs"] = {}
        for name in specs:
            _json["output_specs"][name] = []
            t_list: List[Type[Resource]] = specs[name]
            if not isinstance(t_list, tuple):
                t_list = (t_list, )

            for resource_type in t_list:
                if resource_type is None:
                    _json["output_specs"][name].append(None)
                else:
                    # set the resource typing name as output_specs
                    _json["output_specs"][name].append(
                        resource_type._typing_name)

        # Handle the config specs
        _json["config_specs"] = model_t.config_specs
        for k in _json["config_specs"]:
            spec = _json["config_specs"][k]
            if "type" in spec and isinstance(spec["type"], type):
                t_str = spec["type"].__name__
                _json["config_specs"][k]["type"] = t_str

        return _json

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns a JSON string or dictionnary representation of the model.
        :return: The representation
        :rtype: `dict`, `str`
        """
        _json: Dict[str, Any] = super().data_to_json(deep=deep, **kwargs)

        # retrieve the process python type
        model_t: Type[Process] = Utils.get_model_type(self.model_type)

       # Other infos
        _json["title"] = model_t._human_name
        _json["description"] = model_t._short_description
        _json["doc"] = inspect.getdoc(model_t)

        return _json
