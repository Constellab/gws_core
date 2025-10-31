

import inspect
from typing import Any, Dict, List, Optional, Type

from peewee import BooleanField, CharField, ModelSelect

from gws_core.core.model.db_field import BaseDTOField, JSONField
from gws_core.core.utils.reflector_helper import ReflectorHelper
from gws_core.model.typing_dto import (SimpleTypingDTO, TypingDTO,
                                       TypingFullDTO, TypingObjectType,
                                       TypingRefDTO, TypingStatus)
from gws_core.model.typing_name import TypingNameObj
from gws_core.model.typing_style import TypingStyle

from ..core.model.base import Base
from ..core.model.model import Model
from ..core.utils.utils import Utils


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
    style: TypingStyle = BaseDTOField(TypingStyle, null=True)

    # Sub type of the object, types will be differents based on object type
    object_sub_type: CharField = CharField(null=True, max_length=20)
    # For process, this is a linked resource to the model (useful for IMPORTER, TRANFORMERS...)
    related_model_typing_name: CharField = CharField(null=True, index=True)

    data: Dict[str, Any] = JSONField(null=True)

    _object_type: TypingObjectType = "MODEL"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.is_saved() and not self.data:
            self.data = {}

    def _get_hierarchy_table(self) -> List[str]:
        model_t: Type = self.get_type()

        if model_t is None:
            raise Exception(f"Can't get the type of the typing {self.typing_name}")
        mro: List[Type] = inspect.getmro(model_t)

        ht: List[str] = []
        for t in mro:
            if issubclass(t, Base):
                ht.append(t.full_classname())
        return ht

    def _set_ancestors(self, ancestors: List[str]) -> None:
        self.data["ancestors"] = ancestors

    def refresh_ancestors(self) -> None:
        self._set_ancestors(self._get_hierarchy_table())

    def get_ancestors(self) -> List[str]:
        return self.data["ancestors"]

    def get_type(self) -> Optional[Type]:
        return Utils.get_model_type(self.model_type)

    def type_exists(self) -> bool:
        """Check if the type exists in the system.
        """
        return self.get_type() is not None

    @property
    def typing_name(self) -> str:
        return TypingNameObj.typing_obj_to_str(self.object_type, self.brick, self.unique_name)

    def get_type_status(self) -> TypingStatus:
        # retrieve the task python type
        model_t: Type[Base] = self.get_type()
        return TypingStatus.OK if model_t is not None else TypingStatus.UNAVAILABLE

    def to_dto(self) -> TypingDTO:
        return TypingDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            unique_name=self.unique_name,
            object_type=self.object_type,
            typing_name=self.typing_name,
            brick_version=self.brick_version,
            human_name=self.human_name,
            short_description=self.short_description,
            object_sub_type=self.object_sub_type,
            deprecated_since=self.deprecated_since,
            deprecated_message=self.deprecated_message,
            additional_data=None,
            status=self.get_type_status(),
            hide=self.hide,
            style=self.style
        )

    def to_simple_dto(self) -> SimpleTypingDTO:
        return SimpleTypingDTO(
            human_name=self.human_name,
            short_description=self.short_description,
        )

    def to_ref_dto(self) -> TypingRefDTO:
        return TypingRefDTO(
            typing_name=self.typing_name,
            brick_version=self.brick_version,
            human_name=self.human_name,
            style=self.style,
            short_description=self.short_description
        )

    def to_full_dto(self) -> TypingFullDTO:
        typing_dto = self.to_dto()

        full_dto = TypingFullDTO(**typing_dto.to_json_dict())

        # retrieve the task python type
        model_t: Type[Base] = self.get_type()

        if model_t:
            full_dto.doc = self.get_model_type_doc()

            # handle parent ref
            parent_typing: Typing = self.get_parent_typing()
            if parent_typing:
                full_dto.parent = parent_typing.to_ref_dto()

        return full_dto

    def get_parent_typing(self) -> Optional['Typing']:
        # retrieve the task python type
        model_t: Type[Base] = self.get_type()

        if model_t is None:
            return None

        parent_class: Type[Base] = model_t.__base__

        # If the parent class has the attribute typing_name, it means that this is a typing
        if hasattr(parent_class, "__typing_name__"):
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

        return ReflectorHelper.get_cleaned_doc_string(model_t)

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
        table_name = 'gws_typing'
        is_table = True
        indexes = (
            (('brick', 'model_name', 'object_type'), True),
        )
