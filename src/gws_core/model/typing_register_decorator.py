

from typing import Any, Type

from gws_core.model.typing import TypingObjectType

from .typing_manager import TypingManager


def TypingDecorator(name_unique: str, object_type: TypingObjectType, hide: bool = False):
    """Decorator to registrer the class as a typing with a typing name

    :param name_unique: unique name in the brick it will define the typing name
    :type name_unique: str
    :param object_type: typing object type
    :type object_type: TypingObjectType
    :param hide: if True the typing class will not be shown to the user when retriving the typings, defaults to False
    :type hide: bool, optional
    """
    def decorator(object_class: Type[Any]):
        register_typing_class(object_class=object_class,
                              object_type=object_type, name_unique=name_unique, hide=hide)
        return object_class
    return decorator


# Save the Typing to the TypingManager and set the _typing_name class property
def register_typing_class(object_class: Type[Any], object_type: TypingObjectType, name_unique: str, hide: bool = False) -> None:
    typing_name: str = TypingManager.register_typing(
        object_type=object_type,  unique_name=name_unique, object_class=object_class,
        hide=hide)

    object_class._typing_name = typing_name
