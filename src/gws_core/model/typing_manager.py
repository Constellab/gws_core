

from typing import Any, Dict, Type

from peewee import ModelSelect

from ..brick.brick_helper import BrickHelper
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.base import Base
from ..core.model.model import Model
from ..core.utils.logger import Logger
from ..model.typing import Typing


class TypingManager:

    # a dictionary to save the types,the key if the full typing name
    _typings_before_save: Dict[str, Typing] = {}

    # Mark as true when the tables exists, the typings can then be saved directly
    _tables_are_created: bool = False

    # use to cache the names to prevent request each time
    _typings_name_cache: Dict[str, Typing] = {}

    @classmethod
    def get_typing_from_name(cls, typing_name: str) -> Typing:
        if typing_name not in cls._typings_name_cache:
            typing: Typing = Typing.get_by_typing_name(typing_name)

            if typing is None:
                raise BadRequestException(
                    f"Can't find the typing with name {typing_name}, did you register the name with corresponding decorator ?")

            cls._typings_name_cache[typing_name] = typing

        return cls._typings_name_cache[typing_name]

    @classmethod
    def get_type_from_name(cls, typing_name: str) -> Type[Any]:
        return cls.get_typing_from_name(typing_name).get_type()

    @classmethod
    def get_object_with_typing_name(cls, typing_name: str, object_id: str) -> Model:
        model_type: Type[Model] = cls.get_type_from_name(typing_name)
        if not issubclass(model_type, Model):
            raise BadRequestException(
                f"Can't get the object of type {model_type} (typing name: {typing_name}) from the DB because it is not a Model")
        return model_type.get_by_id(object_id)

    @classmethod
    def get_object_with_typing_name_and_id(cls, typing_name: str, id: str) -> Model:
        model_type: Type[Model] = cls.get_type_from_name(typing_name)
        if not issubclass(model_type, Model):
            raise BadRequestException(
                f"Can't get the object of type {model_type} (typing name: {typing_name}) from the DB because it is not a Model")

        return model_type.get_by_id(id)

    @classmethod
    def type_is_register(cls, model_type: Type[Base]) -> bool:
        return Typing.type_is_register(model_type=model_type)

    @classmethod
    def register_typing(cls, typing: Typing, object_class: Type[Base]) -> None:
        """Register the typing into the manager to save it in the database
        Return the typing unique name
        """

        if not issubclass(object_class, Base):
            name = object_class.__name__ if object_class.__name__ is not None else str(
                object_class)
            raise Exception(
                f"""Trying to register the type {name} but it is not a subclass of Base""")

        if typing.typing_name in cls._typings_before_save:
            raise Exception(
                f"""2 differents {typing.object_type} in the brick {typing.brick} register with the same name : {typing.model_name}.
                                {typing.object_type} already register: [{cls._typings_before_save[typing.typing_name]['model_type'] }].
                                {typing.object_type} trying to register : {object_class.full_classname()}
                                Please update one of the unique name""")

        cls._typings_before_save[typing.typing_name] = typing

        # If the tables exists, directly create the typing
        if cls._tables_are_created:
            cls._save_object_type_in_db(typing)

    @classmethod
    def save_object_types_in_db(cls) -> None:
        # once this method is called, we considere the tables are ready
        cls._tables_are_created = True

        for typing in cls._typings_before_save.values():
            cls._save_object_type_in_db(typing)

    @classmethod
    def _save_object_type_in_db(cls, typing: Typing) -> None:
        query: ModelSelect = Typing.get_by_brick_and_model_name(
            typing.object_type, typing.brick, typing.model_name)

        # set the version because the bricks are not loaded before
        brick_info = BrickHelper.get_brick_info(typing.brick)
        typing.brick_version = brick_info["version"]

        # refresh or set the ancestors list
        typing.refresh_ancestors()

        # If it doesn't exist, create the type in DB
        if query.count() == 0:
            # force the creation (useful for tests when this is called multiple time with the same objects)
            typing.save(force_insert=True)
            return

        typing_db: Typing = query.first()

        # If the model type has changed, log a message and update the DB
        if typing_db.model_type != typing.model_type or typing_db.related_model_typing_name != typing.related_model_typing_name or \
                typing_db.object_sub_type != typing.object_sub_type or str(typing_db.data) != str(typing.data):
            Logger.info(f"""Typing {typing.model_name} in brick {typing.brick} has changed.""")
            cls._update_typing(typing, typing_db)
            return

        # If another value has changed only udpate the DB
        if typing_db.hide != typing.hide or typing_db.human_name != typing.human_name or typing_db.short_description != typing.short_description or \
                typing_db.deprecated_since != typing.deprecated_since or typing_db.deprecated_message != typing.deprecated_message or \
                typing_db.brick_version != typing.brick_version:
            cls._update_typing(typing, typing_db)
            return

    @classmethod
    def _update_typing(cls, typing: Typing, typing_db: Typing) -> None:
        typing.id = typing_db.id
        typing.save(force_insert=False)  # use to update instead of insert

    @classmethod
    def get_typings(cls) -> Dict[str, Typing]:
        return cls._typings_before_save
