

from typing import Dict, Type, TypedDict

from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from peewee import ModelSelect

from ..core.model.base import Base
from ..core.model.model import Model
from ..core.utils.logger import Logger
from ..core.utils.utils import Utils
from ..model.typing import Typing, TypingObjectType, build_typing_unique_name


# Use to store locaaly the typing information
class TypingLocal(TypedDict):
    model_type: str
    brick: str
    model_name: str
    object_type: TypingObjectType
    human_name: str
    short_description: str
    hide: bool


class TypingManager:

    # a dictionary to save the types,the first key is the object type, the key is the brick name, the second the model type
    _typings: Dict[TypingObjectType, Dict[str, Dict[str, TypingLocal]]] = {}

    # Mark as true when the tables exists, the typings can then be saved directly
    _tables_are_created: bool = False

    @classmethod
    def get_type_from_name(cls, typing_name: str) -> Type[Model]:
        typing: Typing = Typing.get_by_typing_name(typing_name).first()

        if typing is None:
            raise BadRequestException(
                f"Can't find the typing with name {typing_name}, did you register the name with corresponding decorator ?")

        return Model.get_model_type(typing.model_type)

    @classmethod
    def get_object_with_typing_name(cls, typing_name: str, id: int) -> Model:
        model_type:  Type[Model] = cls.get_type_from_name(typing_name)
        return model_type.get_by_id(id)

    @classmethod
    def get_object_with_typing_name_and_uri(cls, typing_name: str, uri: str) -> Model:
        model_type:  Type[Model] = cls.get_type_from_name(typing_name)
        return model_type.get_by_uri(uri)

    @classmethod
    def type_is_register(cls, model_type: Type[Model]) -> bool:
        return Typing.get_by_model_type(model_type=model_type).count() > 0

    @classmethod
    def register_typing(cls, object_type: TypingObjectType,  unique_name: str, object_class: Type[Model], human_name: str, short_description: str, hide: bool) -> str:
        """Register the typing into the manager to save it in the database
        Return the typing unique name
        """

        if not issubclass(object_class, Base):
            name = object_class.__name__ if object_class.__name__ is not None else str(
                object_class)
            raise Exception(
                f"""Trying to register the type {name} but it is not a subclass of Base""")

        brick_name: str = Utils.get_brick_name(object_class)

        if not object_type in cls._typings:
            cls._typings[object_type] = {}

        if not brick_name in cls._typings[object_type]:
            cls._typings[object_type][brick_name] = {}

        if unique_name in cls._typings[object_type][brick_name]:
            raise Exception(f"""2 differents {object_type} in the brick {brick_name} register with the same name : {unique_name}.
                                {object_type} already register: [{cls._typings[object_type][brick_name][unique_name]['model_type'] }].
                                {object_type} trying to register : {object_class.full_classname()}
                                Please update one of the unique name""")

        # add the object type to the list
        typing_local: TypingLocal = TypingLocal(
            brick=brick_name,
            model_name=unique_name,
            model_type=object_class.full_classname(),
            object_type=object_type,
            human_name=human_name,
            short_description=short_description,
            hide=hide,
        )

        cls._typings[object_type][brick_name][unique_name] = typing_local

        # If the tables exists, directly create the typing
        if cls._tables_are_created:
            cls._save_object_type_in_db(typing_local)

        return build_typing_unique_name(typing_local['object_type'], typing_local['brick'], typing_local['model_name'])

    @classmethod
    def save_object_types_in_db(cls) -> None:
        # once this method is called, we considere the tables are ready
        cls._tables_are_created = True

        for bricks in cls._typings.values():
            for objects in bricks.values():
                for typing in objects.values():
                    cls._save_object_type_in_db(typing)

    @classmethod
    def _save_object_type_in_db(cls, typing_local: TypingLocal) -> None:
        typing = Typing(
            brick=typing_local['brick'],
            model_name=typing_local['model_name'],
            model_type=typing_local['model_type'],
            object_type=typing_local['object_type'],
            human_name=typing_local['human_name'],
            short_description=typing_local['short_description'],
            hide=typing_local['hide']
        )

        query: ModelSelect = Typing.get_by_brick_and_model_name(
            typing.object_type, typing.brick, typing.model_name)

        # If it doesn't exist, create the type in DB
        if query.count() == 0:
            typing.save()
            return

        typing_db: Typing = query.first()

        # If the model type has changed, log a message and update the DB
        if typing_db.model_type != typing.model_type:
            Logger.info(f"""object_type type {typing.model_name} in brick {typing.brick} has changed its model type.
                            Previous value {typing_db.model_type}.
                            New Value {typing.model_type}""")
            typing_db.update_model_type(typing.model_type)
            return

        # If the data has changed, log a message and update the DB
        if str(typing_db.data) != str(typing.data):
            Logger.info(f"""{typing_db.model_type} type {typing.model_name} in brick {typing.brick} has changed its data.
                            Previous value {typing_db.data}.
                            New Value {typing.data}""")
            typing_db.data = typing.data
            typing_db.save()
            return

        # If another value has changed only udpate the DB
        if typing_db.hide != typing.hide or typing_db.human_name != typing.human_name or typing_db.short_description != typing.short_description:
            typing_db.hide = typing.hide
            typing_db.human_name = typing.human_name
            typing_db.short_description = typing.short_description
            typing_db.save()
            return

    @classmethod
    def get_typings(cls) -> Dict[TypingObjectType, Dict[str, Dict[str, TypingLocal]]]:
        return cls._typings
