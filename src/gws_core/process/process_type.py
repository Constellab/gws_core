# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List, Type, final

from peewee import ModelSelect

from ..config.config_spec import ConfigSpecs
from ..core.utils.utils import Utils
from ..io.io_types import IOSpecs
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

        if deep:
            # retrieve the process python type
            model_t: Type[Process] = Utils.get_model_type(self.model_type)

            # Handle the resource input specs
            _json["input_specs"] = self._io_specs_to_json(model_t.input_specs)

            # Handle the resource output specs
            _json["output_specs"] = self._io_specs_to_json(model_t.output_specs)

            # Handle the config specs
            _json["config_specs"] = self._config_specs_to_json(model_t.config_specs)

        return _json

    def _io_specs_to_json(self, specs: IOSpecs) -> dict:
        _json = {}
        for name in specs:
            _json[name] = []
            t_list: List[Type[Resource]] = specs[name]
            if not isinstance(t_list, tuple):
                t_list = (t_list, )

            for resource_type in t_list:
                if resource_type is None:
                    _json[name].append(None)
                else:
                    # set the resource typing name as input_spec
                    _json[name].append(
                        resource_type._typing_name)

        return _json

    def _config_specs_to_json(self, specs: ConfigSpecs) -> Dict:
        _json = {}
        for key, spec in specs.items():
            _json[key] = spec
            if "type" in spec and isinstance(spec["type"], type):
                _json[key]["type"] = spec["type"].__name__
        return _json

    def data_to_json(self, deep: bool = False, **kwargs) -> dict:
        """
        Returns a JSON string or dictionnary representation of the model.
        :return: The representation
        :rtype: `dict`, `str`
        """

        if not deep:
            return None

        _json: Dict[str, Any] = super().data_to_json(deep=deep, **kwargs)

       # Other infos
        _json["doc"] = self.get_model_type_doc()

        return _json
