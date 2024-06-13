

from typing import Dict, Optional, Type

from peewee import ModelSelect

from gws_core.model.typing_exception import TypingNotFoundException
from gws_core.model.typing_name import TypingNameObj

from ..brick.brick_helper import BrickHelper
from ..core.exception.exceptions.bad_request_exception import \
    BadRequestException
from ..core.model.base import Base
from ..core.model.model import Model
from ..core.utils.logger import Logger
from ..model.typing import Typing


class TypingManager:

    # Mark as true when the tables exists, the typings can then be saved directly
    _tables_are_created: bool = False

    # use to cache the names to prevent request each time
    _typings_name_cache: Dict[str, Typing] = {}

    @classmethod
    def get_typing_from_name(cls, typing_name: str) -> Optional[Typing]:
        """Get typing from name and return None if not found"""
        if typing_name not in cls._typings_name_cache:
            typing: Typing = Typing.get_by_typing_name(typing_name)

            if typing is None:
                return None

            cls._typings_name_cache[typing_name] = typing

        return cls._typings_name_cache[typing_name]

    @classmethod
    def get_typing_from_name_and_check(cls, typing_name: str) -> Typing:
        """Get typing from name and check if it exists"""
        typing: Optional[Typing] = cls.get_typing_from_name(typing_name)

        if typing is None:
            raise TypingNotFoundException(typing_name)
        return typing

    @classmethod
    def get_type_from_name(cls, typing_name: str) -> Optional[Type]:
        return cls.get_typing_from_name_and_check(typing_name).get_type()

    @classmethod
    def get_and_check_type_from_name(cls, typing_name: str) -> Type:
        type_ = cls.get_type_from_name(typing_name)

        if type_ is None:
            raise TypingNotFoundException(typing_name)

        return type_

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

        if typing.typing_name in cls._typings_name_cache:
            raise Exception(
                f"""2 differents {typing.object_type} in the brick {typing.brick} register with the same name : {typing.unique_name}.
                                {typing.object_type} already register: [{cls._typings_name_cache[typing.typing_name].model_type }].
                                {typing.object_type} trying to register : {object_class.full_classname()}
                                Please update one of the unique name""")

        cls._typings_name_cache[typing.typing_name] = typing

        # If the tables exists, directly create the typing
        if cls._tables_are_created:
            cls._save_object_type_in_db(typing)

    @classmethod
    def save_object_types_in_db(cls) -> None:
        # once this method is called, we considere the tables are ready
        cls._tables_are_created = True

        for typing in cls._typings_name_cache.values():
            cls._save_object_type_in_db(typing)

    @classmethod
    def init_typings(cls) -> None:
        """Call this method after all the bricks are loaded to refresh the ancestors list and brick version of typing
        """
        for typing in cls._typings_name_cache.values():
            cls._init_typing(typing)

    @classmethod
    def _init_typing(cls, typing: Typing) -> None:
        """Call this method after all the bricks are loaded to refresh the ancestors list and brick version of typing
        """
        if not typing.brick_version:
            # set the version because the bricks might not be loaded before
            # if this is the first start
            brick_info = BrickHelper.get_brick_info(typing.brick)
            if brick_info is None:
                Logger.error(
                    f"Can't get the brick info for brick '{typing.brick}' of typing '{typing.typing_name}'. Is the file in the correct folder in your brick ? Skipping the typing")
            else:
                typing.brick_version = brick_info.version

        # refresh the ancestor list once all the type are loaded
        typing.refresh_ancestors()

    @classmethod
    def _save_object_type_in_db(cls, typing: Typing) -> None:
        try:
            cls._init_typing(typing)

            query: ModelSelect = Typing.get_by_brick_and_unique_name(
                typing.object_type, typing.brick, typing.unique_name)
            # If it doesn't exist, create the type in DB
            if query.count() == 0:
                # force the creation (useful for tests when this is called multiple time with the same objects)
                typing.save(force_insert=True)
                # replace in the cache
                cls._typings_name_cache[typing.typing_name] = typing
                return

            typing_db: Typing = query.first()
            typing.id = typing_db.id  # use the same id
            typing_db = typing.save(force_insert=False)

            # replace in the cache
            cls._typings_name_cache[typing.typing_name] = typing_db

        except Exception as err:
            Logger.error(f"Error while saving the typing '{typing.typing_name}', skipping the typing. Error : {err}")

    @classmethod
    def check_typing_name_compatibility(cls, typing_name: str) -> None:
        """Method to check if the typing name is compatible with the current lab
        """
        if not typing_name:
            raise Exception('The typing name is empty.')
        typing = TypingNameObj.from_typing_name(typing_name)

        if not BrickHelper.brick_is_loaded(typing.brick_name):
            raise Exception(f'Brick {typing.brick_name} is not loaded.')

        # check that the type exist
        TypingManager.get_typing_from_name_and_check(typing_name)
