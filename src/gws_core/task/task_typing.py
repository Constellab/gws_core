# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import List, Literal, Type, final

from gws_core.core.utils.utils import Utils
from gws_core.process.process_types import ProcessSpecDict
from gws_core.resource.resource import Resource
from peewee import CharField, Expression, ModelSelect

from ..config.config_specs_helper import ConfigSpecsHelper
from ..io.io_spec_helper import IOSpecsHelper
from ..model.typing import Typing
from ..model.typing_dict import TypingObjectType
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

        # filter on object type and related_model_typing_name
        return list(
            cls.select().where(
                (cls.object_type == cls._object_type) & (cls.object_sub_type == task_sub_type) &
                (cls.get_related_model_expression(resource_type)))
            .order_by(cls.human_name)
        )

    @classmethod
    def get_related_model_expression(cls, related_model_type: Type[Resource]) -> Expression:
        """Return an expression for a model select that will return all the task types
        related to a resource type or its parent classes"""
        # get all the class types between base_type and Model
        parent_classes: List[Type[Resource]] = Utils.get_parent_classes(related_model_type, Resource)

        typings_names = [parent._typing_name for parent in parent_classes]

        return cls.related_model_typing_name.in_(typings_names)

    @classmethod
    def get_by_brick(cls, brick_name: str) -> List['TaskTyping']:
        return cls.get_by_type_and_brick(cls._object_type, brick_name)

    def importer_extension_is_supported(self, extension: str) -> bool:
        """Function that works only for IMPORTERS. It returns True if the extension is supported by the importer
        """
        from ..task.converter.importer import ResourceImporter
        type_: Type[ResourceImporter] = self.get_type()

        if type_ is None or not Utils.issubclass(type_, ResourceImporter):
            return False

        # if the importer does not as supported extension, we consider all the extension as supported
        if not type_._supported_extensions:
            return True

        return extension in type_._supported_extensions

    def to_json(self, deep: bool = False, **kwargs) -> ProcessSpecDict:
        json_: ProcessSpecDict = super().to_json(deep=deep, **kwargs)

        if deep:
            # retrieve the task python type
            model_t: Type[Task] = self.get_type()

            if model_t:
                json_["input_specs"] = IOSpecsHelper.io_specs_to_json(model_t.input_specs)
                json_["output_specs"] = IOSpecsHelper.io_specs_to_json(model_t.output_specs)
                json_["config_specs"] = ConfigSpecsHelper.config_specs_to_json(model_t.config_specs)

        return json_
