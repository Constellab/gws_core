# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Any, Dict, List, Literal, Type, final

from gws_core.core.utils.utils import Utils
from gws_core.resource.resource import Resource
from peewee import CharField, ModelSelect

from ..config.config_specs_helper import ConfigSpecsHelper
from ..io.io_spec_helper import IOSpecsHelper
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

    @classmethod
    def get_by_brick(cls, brick_name: str) -> List['TaskTyping']:
        return cls.get_by_type_and_brick(cls._object_type, brick_name)

    def model_type_to_json(self, model_t: Type[Task]) -> dict:
        return {
            "input_specs": IOSpecsHelper.io_specs_to_json(model_t.input_specs),
            "output_specs": IOSpecsHelper.io_specs_to_json(model_t.output_specs),
            "config_specs": ConfigSpecsHelper.config_specs_to_json(model_t.config_specs),
            "doc": self.get_model_type_doc(),
        }
