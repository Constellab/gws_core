# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
from typing import Any, Dict, List, Literal, Type, Union

from peewee import BooleanField, CharField, ModelSelect

from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.model import Model

# ####################################################################
#
# ProcessType class
#
# ####################################################################
SEPARATOR: str = "."

# different object typed store in the typing table
TypingObjectType = Literal["PROCESS", "RESOURCE", "PROTOCOL", "GWS_CORE"]
available_object_types = ["PROCESS", "RESOURCE", "PROTOCOL", "GWS_CORE"]


# Simple method to build the typing  = object_type.brick.model_name
def build_typing_unique_name(object_type: str, brick_name: str, model_name: str) -> str:
    return object_type + SEPARATOR + brick_name + SEPARATOR + model_name


class Typing(Model):
    """
    Typing class. This class allows storing information on all the types of the models in the system.

    :property type: The type of the related model.
    :type type: `str`
    :property super_type: The super type of the related model.
    :type super_type: `str`
    :property root_type: The root type of the related process.
    :type root_type: `str`
    """

    # Full python type of the model
    model_type: CharField = CharField(null=False)
    brick: CharField = CharField(null=False, index=True)
    model_name: CharField = CharField(null=False, index=True)
    object_type: CharField = CharField(null=False)
    human_name: CharField = CharField(default=False)
    short_description: CharField = CharField(default=False)
    hide: BooleanField = BooleanField(default=False)

    _table_name = 'gws_typing'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.object_type not in available_object_types:
            raise BadRequestException(
                f"The type {self.object_type} is not authorized in Typing, possible values: {available_object_types}")

        if not self.data.get("ancestors"):
            self._set_ancestors(self.__get_hierarchy_table())

    # -- G --

    def get_model_types_array(self) -> List[str]:
        """
        Return the model_type as an array by splitting with .
        """

        return self.model_type.split('.')

    def __get_hierarchy_table(self) -> List[str]:
        model_t: Model = self.get_model_type(self.model_type)
        mro: List[Model] = inspect.getmro(model_t)

        ht: List[str] = []
        for t in mro:
            if issubclass(t, Model):
                ht.append(t.full_classname())

        return ht

    def update_model_type(self, model_type) -> 'Typing':
        """
        Update the model type and the ancestors, then save into the DB
        """
        self.model_type = model_type
        self._set_ancestors(self.__get_hierarchy_table())

        self.save()
        return self

    def _set_ancestors(self, ancestors: List[str]) -> None:
        self.data["ancestors"] = ancestors

    @property
    def typing_name(self) -> str:
        return build_typing_unique_name(self.object_type, self.brick, self.model_name)

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
                f"The typing name {typing_name} in invalid")
        return cls.get_by_brick_and_model_name(object_type, brick_name,  model_name)

    @classmethod
    def get_by_object_type(cls, object_type: TypingObjectType) -> ModelSelect:
        return cls.select()\
            .where((cls.object_type == object_type) & (cls.hide == False))\
            .order_by(cls.model_type.desc())

    @classmethod
    def get_by_model_type(cls, model_type: Type[Model]) -> ModelSelect:
        return cls.select().where((cls.model_type == model_type.full_classname()))

    def to_json(self, deep: bool = False, **kwargs) -> dict:
        _json: Dict[str, Any] = super().to_json(deep=deep, **kwargs)

        _json["typing_name"] = self.typing_name
        return _json

    class Meta:
        # Unique constrains on brick, model_name and object_type
        indexes = (
            (('brick', 'model_name', 'object_type'), True),
        )
