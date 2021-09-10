# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, Type, final

from peewee import ModelSelect

from ..config.config_spec import ConfigSpecsHelper
from ..core.utils.utils import Utils
from ..io.io_spec import IOSpecsHelper
from ..model.typing import Typing, TypingObjectType
from ..task.task import Task


@final
class TaskTyping(Typing):
    """
    TaskTyping class.
    """

    _object_type: TypingObjectType = "TASK"

    @classmethod
    def get_types(cls) -> ModelSelect:
        return cls.get_by_object_type(cls._object_type)

    def to_json(self, deep: bool = False, **kwargs) -> dict:

        _json: Dict[str, Any] = super().to_json(deep=deep, **kwargs)

        # TODO to remove | for compatibility
        _json["ptype"] = self.model_type

        if deep:
            # retrieve the task python type
            model_t: Type[Task] = Utils.get_model_type(self.model_type)

            # Handle the resource input specs
            _json["input_specs"] = IOSpecsHelper.io_specs_to_json(model_t.input_specs)

            # Handle the resource output specs
            _json["output_specs"] = IOSpecsHelper.io_specs_to_json(model_t.output_specs)

            # Handle the config specs
            _json["config_specs"] = ConfigSpecsHelper.config_specs_to_json(model_t.config_specs)

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
