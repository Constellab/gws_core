from typing import List, Literal, Set, Type, Union, final

from gws_core.core.utils.utils import Utils
from gws_core.resource.resource import Resource
from gws_core.task.task_dto import TaskTypingDTO
from peewee import CharField, Expression, ModelSelect

from ..model.typing import Typing
from ..model.typing_dto import TypingObjectType
from ..task.task import Task

TaskSubType = Literal["TASK", "IMPORTER", "EXPORTER", "TRANSFORMER", "ACTIONS_TASK"]


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
    def get_by_related_resource(
        cls, resource_type: Type[Resource], task_sub_type: TaskSubType
    ) -> List["TaskTyping"]:
        # filter on object type and related_model_typing_name
        return list(
            cls.select()
            .where(
                (cls.object_type == cls._object_type)
                & (cls.object_sub_type == task_sub_type)
                & (cls.get_related_model_expression(resource_type))
            )
            .order_by(cls.human_name)
        )

    @classmethod
    def get_related_model_expression(
        cls, related_model_types: Union[Type[Resource], List[Type[Resource]]]
    ) -> Expression:
        """Return an expression for a model select that will return all the task types
        related to a resource type or its parent classes

        It can take a single or a list of resource types

        """

        if not isinstance(related_model_types, list):
            related_model_types = [related_model_types]

        parent_typing_names: Set[str] = set()

        for related_model_type in related_model_types:
            # get all the class types between base_type and Resource
            parent_classes: List[Type[Resource]] = Utils.get_parent_classes(
                related_model_type, Resource
            )
            # add typing name to the set
            parent_typing_names = parent_typing_names.union(
                [parent.get_typing_name() for parent in parent_classes]
            )

        return cls.related_model_typing_name.in_(parent_typing_names)

    @classmethod
    def get_by_brick(cls, brick_name: str) -> List["TaskTyping"]:
        return cls.get_by_type_and_brick(cls._object_type, brick_name)

    def importer_extension_is_supported(self, extension: str) -> bool:
        """Function that works only for IMPORTERS. It returns True if the extension is supported by the importer"""
        from ..task.converter.importer import ResourceImporter

        type_: Type[ResourceImporter] = self.get_type()

        if type_ is None or not Utils.issubclass(type_, ResourceImporter):
            return False

        # if the importer does not as supported extension, we consider all the extension as supported
        if not type_.__supported_extensions__:
            return True

        return extension in type_.__supported_extensions__

    def to_full_dto(self) -> TaskTypingDTO:
        typing_dto = super().to_full_dto()

        task_typing = TaskTypingDTO(
            **typing_dto.to_json_dict(),
        )

        # retrieve the task python type
        model_t: Type[Task] = self.get_type()

        if model_t:
            task_typing.input_specs = model_t.input_specs.to_dto()
            task_typing.output_specs = model_t.output_specs.to_dto()
            task_typing.config_specs = model_t.config_specs.to_dto()

            from ..task.converter.importer import ResourceImporter

            if Utils.issubclass(model_t, ResourceImporter):
                importer_t: Type[ResourceImporter] = model_t
                task_typing.additional_data = {
                    "supported_extensions": importer_t.__supported_extensions__
                }

        return task_typing

    class Meta:
        is_table = False
        table_name = "gws_typing"
