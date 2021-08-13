

from typing import Any, Callable, Type

from gws_core.model.typing import TypingObjectType

from .typing_manager import TypingManager


def TypingDecorator(unique_name: str, object_type: TypingObjectType, hide: bool = False) -> Callable:
    """Decorator to register the class as a typing with a typing name

    param name_unique: a unique name for this protocol in the brick. Only 1 protocol in the current brick can have this name.
                        /!\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED /!\
                        It is used to instantiate the protocols
    :type name_unique: str
    :param object_type: typing object type
    :type object_type: TypingObjectType
    :param hide: if True the typing class will not be shown to the user when retriving the typings, defaults to False
    :type hide: bool, optional
    """
    def decorator(object_class: Type[Any]):
        register_typing_class(object_class=object_class,
                              object_type=object_type, unique_name=unique_name,
                              human_name="", short_description="", hide=hide)
        return object_class
    return decorator


# Save the Typing to the TypingManager and set the _typing_name class property
def register_typing_class(object_class: Type[Any], object_type: TypingObjectType, unique_name: str, human_name: str, short_description, hide: bool = False) -> None:
    typing_name: str = TypingManager.register_typing(
        object_type=object_type,  unique_name=unique_name, object_class=object_class,
        human_name=human_name, short_description=short_description,  hide=hide)

    object_class._typing_name = typing_name
