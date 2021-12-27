# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List, Literal, Type, final

from gws_core.core.utils.utils import Utils
from gws_core.resource.resource import Resource
from peewee import CharField, ModelSelect

from ..config.config_types import ConfigSpecsHelper
from ..io.io_spec import IOSpecsHelper
from ..model.typing import Typing, TypingObjectType
from ..task.task import Task

TaskSubType = Literal["TASK", "IMPORTER", "EXPORTER", "TRANSFORMER"]


@final
class TaskTyping(Typing):
    """
    TaskTyping class.
    """

    # Sub type of the object, types will be differents based on object type
    object_sub_type: TaskSubType = CharField(null=True, max_length=20)

    _object_type: TypingObjectType = "TASK"

    @classmethod
    def get_types(cls) -> ModelSelect:
        return cls.get_by_object_type(cls._object_type)

    @classmethod
    def get_by_related_resource(cls, resource_type: Type[Resource], task_sub_type: TaskSubType) -> List['TaskTyping']:
        # get all the class types between base_type and Model
        parent_classes: List[Type[Resource]] = Utils.get_parent_classes(resource_type, Resource)

        # retrieve the class typing_names
        typing_names = list(map(lambda type_: type_._typing_name, parent_classes))

        # filter on object type and related_model_typing_name
        return list(
            cls.select().where(
                (cls.object_type == cls._object_type) & (cls.object_sub_type == task_sub_type) &
                (cls.related_model_typing_name.in_(typing_names)))
            .order_by(cls.human_name)
        )

    def to_json(self, deep: bool = False, **kwargs) -> dict:

        _json: Dict[str, Any] = super().to_json(deep=deep, **kwargs)

        if deep:
            # retrieve the task python type
            model_t: Type[Task] = self.get_type()

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
