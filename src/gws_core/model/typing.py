# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import inspect
from typing import Any, Dict, List, Optional, Type

from peewee import BooleanField, CharField, ModelSelect

from gws_core.brick.brick_helper import BrickHelper
from gws_core.model.typing_name import TypingNameObj

from ..core.decorator.json_ignore import json_ignore
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.base import Base
from ..core.model.model import Model
from ..core.utils.utils import Utils
from .typing_dict import TypingDict, TypingObjectType, TypingRef, TypingStatus

# ####################################################################
#
# ProcessType class
#
# ####################################################################
SEPARATOR: str = "."


@json_ignore(["model_type", "related_model_typing_name", "data", "brick", "brick_version", "is_archived"])
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
    brick_version: CharField = CharField(null=False, max_length=50, default="")
    unique_name: CharField = CharField(null=False, column_name="model_name")
    object_type: CharField = CharField(null=False, max_length=20)
    human_name: CharField = CharField(default=False, max_length=255)
    short_description: CharField = CharField(default=False)
    deprecated_since: CharField = CharField(null=True, max_length=50)
    deprecated_message: CharField = CharField(null=True, max_length=255)
    hide: BooleanField = BooleanField(default=False)

    # Sub type of the object, types will be differents based on object type
    object_sub_type: CharField = CharField(null=True, max_length=20)
    # For process, this is a linked resource to the model (useful for IMPORTER, TRANFORMERS...)
    related_model_typing_name: CharField = CharField(null=True, index=True)

    _object_type: TypingObjectType = "MODEL"
    _table_name = 'gws_typing'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not Utils.value_is_in_literal(self.object_type, TypingObjectType):
            raise BadRequestException(
                f"The type {self.object_type} is not authorized in Typing, possible values: {Utils.get_literal_values(TypingObjectType)}")

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

    def update_model_type(self, model_type) -> None:
        """
        Update the model type and the ancestors, then save into the DB
        """
        self.model_type = model_type
        self.refresh_ancestors()

    def _set_ancestors(self, ancestors: List[str]) -> None:
        self.data["ancestors"] = ancestors

    def refresh_ancestors(self) -> None:
        self._set_ancestors(self._get_hierarchy_table())

    def get_ancestors(self) -> List[str]:
        return self.data["ancestors"]

    def get_type(self) -> Type:
        return Utils.get_model_type(self.model_type)

    def get_typing_ref(self) -> TypingRef:
        return {
            "typing_name": self.typing_name,
            "brick_version": self.brick_version,
            "human_name": self.human_name
        }

    @property
    def typing_name(self) -> str:
        return TypingNameObj.typing_obj_to_str(self.object_type, self.brick, self.unique_name)

    def get_type_status(self) -> TypingStatus:
        # retrieve the task python type
        model_t: Type[Base] = self.get_type()
        return TypingStatus.OK if model_t is not None else TypingStatus.UNAVAILABLE

    def to_json(self, deep: bool = False, **kwargs) -> TypingDict:
        _json: Dict[str, Any] = super().to_json(deep=deep, **kwargs)

        _json["typing_name"] = self.typing_name

        # retrieve the task python type
        model_t: Type[Base] = self.get_type()
        _json["status"] = self.get_type_status()

        if deep and model_t:
            _json['doc'] = self.get_model_type_doc()

            # handle parent ref
            parent_typing: Typing = self.get_parent_typing()
            if parent_typing:
                parent: TypingRef = parent_typing.get_typing_ref()
            else:
                parent = None
            _json["parent"] = parent

        brick_info = BrickHelper.get_brick_info(self.brick)
        if brick_info:
            _json["brick_version"] = brick_info["version"]

        return _json

    def get_parent_typing(self) -> Optional['Typing']:
        # retrieve the task python type
        model_t: Type[Base] = self.get_type()

        if model_t is None:
            return None

        parent_class: Type[Base] = model_t.__base__

        # If the parent class has the attribute _typing_name, it means that this is a typing
        if hasattr(parent_class, "_typing_name"):
            # retrieve the typing of the parent class
            return Typing.get_by_model_type(parent_class)
        return None

    def get_model_type_doc(self) -> str:
        """Return the python documentation of the model type
        """

        # retrieve the task python type
        model_t: Type[Base] = self.get_type()

        if model_t is None:
            return ""
        return inspect.getdoc(model_t)

    ############################################# CLASS METHODS #########################################

    @classmethod
    def get_by_brick_and_unique_name(cls, object_type: TypingObjectType, brick: str, unique_name: str) -> ModelSelect:
        return cls.select().where(
            cls.object_type == object_type, cls.brick == brick, cls.unique_name == unique_name)

    @classmethod
    def get_by_typing_name(cls, typing_name: str) -> 'Typing':
        typing_obj: TypingNameObj = TypingNameObj.from_typing_name(typing_name)
        return cls.get_by_brick_and_unique_name(
            typing_obj.object_type, typing_obj.brick_name, typing_obj.unique_name).first()

    @classmethod
    def get_by_object_type(cls, object_type: TypingObjectType) -> ModelSelect:
        """ Return all the visible typing name of a type.
        """
        return cls.select()\
            .where((cls.object_type == object_type) & (cls.hide == False))\
            .order_by(cls.human_name)

    @classmethod
    def get_by_object_type_and_name(cls, object_type: TypingObjectType, name: str) -> ModelSelect:
        """ Return all the visible typing name of a type searched by name.
        """
        return cls.select()\
            .where((cls.object_type == object_type) & (cls.hide == False) &
                   (cls.unique_name.contains(name) | cls.human_name.contains(name)))\
            .order_by(cls.human_name)

    @classmethod
    def get_by_type_and_brick(cls, object_type: TypingObjectType, brick_name: str) -> ModelSelect:
        """ Return all the visible typing name of a type.
        """
        return cls.select()\
            .where((cls.object_type == object_type) & (cls.brick == brick_name))\
            .order_by(cls.human_name)

    @classmethod
    def get_by_object_sub_type(cls, sub_type: str) -> List['Typing']:
        return list(cls.select().where(cls.object_sub_type == sub_type).order_by(cls.human_name))

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
    def get_by_brick_and_object_type(cls, brick_name: str) -> List['Typing']:
        return cls.get_by_type_and_brick(cls._object_type, brick_name)

    @classmethod
    def get_children_typings(cls, typing_type: TypingObjectType,  base_type: Type[Base]) -> List['Typing']:
        """Retunr the list of typings that are a child class of the provided model_type
        """
        all_typings: List[Typing] = list(cls.get_by_object_type(typing_type))

        typings = list(filter(lambda typing: Utils.issubclass(typing.get_type(), base_type), all_typings))
        return typings

    @classmethod
    def after_table_creation(cls) -> None:
        super().after_table_creation()
        cls.create_full_text_index(['human_name', 'short_description', 'model_name'], 'I_F_TYP_TXT')
    ############################################# STATIC METHODS #########################################

    @staticmethod
    def typing_name_is_protocol(typing_name: str) -> bool:
        return typing_name.startswith("PROTOCOL")

    class Meta:
        # Unique constrains on brick, model_name and object_type
        indexes = (
            (('brick', 'model_name', 'object_type'), True),
        )
