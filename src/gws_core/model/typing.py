# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
from typing import Any, Dict, List, Literal, Set, Type

from peewee import BooleanField, CharField, ModelSelect

from ..core.decorator.json_ignore import json_ignore
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.base import Base
from ..core.model.model import Model
from ..core.utils.utils import Utils

# ####################################################################
#
# ProcessType class
#
# ####################################################################
SEPARATOR: str = "."

# different object typed store in the typing table
TypingObjectType = Literal["TASK", "RESOURCE", "PROTOCOL", "MODEL"]


# Simple method to build the typing  = object_type.brick.model_name
def build_typing_unique_name(object_type: str, brick_name: str, model_name: str) -> str:
    return object_type + SEPARATOR + brick_name + SEPARATOR + model_name


@json_ignore(["model_type", "hide"])
class Typing(Model):
    """
    Typing class. This class allows storing information on all the types of the models in the system.

    :property type: The type of the related model.
    :type type: `str`
    :property super_type: The super type of the related model.
    :type super_type: `str`
    :property root_type: The root type of the related task.
    :type root_type: `str`
    """

    # Full python type of the model
    model_type: CharField = CharField(null=False, max_length=511)
    brick: CharField = CharField(null=False, max_length=50)
    model_name: CharField = CharField(null=False)
    object_type: CharField = CharField(null=False, max_length=20)
    human_name: CharField = CharField(default=False, max_length=20)
    short_description: CharField = CharField(default=False)
    hide: BooleanField = BooleanField(default=False)

    # Sub type of the object, types will be differents based on object type
    object_sub_type: CharField = CharField(null=True, max_length=20)
    # For process, this is a linked resource to the model (useful for IMPORTER, TRANFORMERS...)
    # For resource, this is a linked resource, useful for importable resource (TableFile is link to Table)
    related_model_typing_name: CharField = CharField(null=True, index=True)

    _table_name = 'gws_typing'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not Utils.value_is_in_literal(self.object_type, TypingObjectType):
            raise BadRequestException(
                f"The type {self.object_type} is not authorized in Typing, possible values: {Utils.get_literal_values(TypingObjectType)}")

    # -- G --

    def get_model_types_array(self) -> List[str]:
        """
        Return the model_type as an array by splitting with .
        """

        return self.model_type.split('.')

    def _get_hierarchy_table(self) -> List[str]:
        model_t: Type = self.get_type()
        mro: List[Type] = inspect.getmro(model_t)

        ht: List[str] = []
        for t in mro:
            if issubclass(t, Base):
                ht.append(t.full_classname())
        return ht

    def update_model_type(self, model_type) -> 'Typing':
        """
        Update the model type and the ancestors, then save into the DB
        """
        self.model_type = model_type
        self.refresh_ancestors()

    def _set_ancestors(self, ancestors: List[str]) -> None:
        self.data["ancestors"] = ancestors

    def refresh_ancestors(self) -> None:
        self._set_ancestors(self._get_hierarchy_table())

    def get_type(self) -> Type[Any]:
        return Utils.get_model_type(self.model_type)

    @property
    def typing_name(self) -> str:
        return build_typing_unique_name(self.object_type, self.brick, self.model_name)

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        _json: Dict[str, Any] = super().to_json(deep=deep, **kwargs)

        _json["typing_name"] = self.typing_name
        return _json

    def get_model_type_doc(self) -> str:
        """Return the python documentation of the model type
        """

        # retrieve the task python type
        model_t: Type[Base] = Utils.get_model_type(self.model_type)
        return inspect.getdoc(model_t)

    ############################################# CLASS METHODS #########################################

    @classmethod
    def get_by_brick_and_model_name(cls, object_type: TypingObjectType, brick: str, model_name: str) -> ModelSelect:
        return Typing.select().where(
            Typing.object_type == object_type, Typing.brick == brick, Typing.model_name == model_name)

    @classmethod
    def get_by_typing_name(cls, typing_name: str) -> ModelSelect:
        # retrieve the brickname and the model name
        try:
            object_type, brick_name, model_name = typing_name.split(SEPARATOR)
        except:
            raise BadRequestException(
                f"The typing name '{typing_name}' is invalid")
        return cls.get_by_brick_and_model_name(object_type, brick_name,  model_name)

    @classmethod
    def get_by_object_type(cls, object_type: TypingObjectType) -> ModelSelect:
        """ Return all the visible typing name of a type.
        """
        return cls.select()\
            .where((cls.object_type == object_type) & (cls.hide == False))\
            .order_by(cls.human_name)

    @classmethod
    def get_by_model_type(cls, model_type: Type[Base]) -> 'Typing':
        return cls._get_by_model_type(model_type).first()

    @classmethod
    def type_is_register(cls, model_type: Type[Base]) -> bool:
        return cls._get_by_model_type(model_type).count() > 0

    @classmethod
    def _get_by_model_type(cls, model_type: Type[Base]) -> ModelSelect:
        return cls.select().where((cls.model_type == model_type.full_classname()))

    @classmethod
    def get_children_typings(cls, typing_type: TypingObjectType,  base_type: Type[Base]) -> List['Typing']:
        """Retunr the list of typings that are a child class of the provided model_type
        """
        all_typings: List[Typing] = list(cls.get_by_object_type(typing_type))

        typings = list(filter(lambda typing: issubclass(typing.get_type(), base_type), all_typings))
        return typings

    class Meta:
        # Unique constrains on brick, model_name and object_type
        indexes = (
            (('brick', 'model_name', 'object_type'), True),
        )
