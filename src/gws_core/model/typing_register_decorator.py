

from typing import Any, Callable, Type

from gws_core.core.utils.utils import Utils

from ..brick.brick_helper import BrickHelper
from ..core.model.base import Base
from ..model.typing import Typing, TypingObjectType
from .typing_manager import TypingManager


def typing_registrator(unique_name: str, object_type: TypingObjectType, hide: bool = False) -> Callable:
    """Decorator to register the class as a typing with a typing name

    param name_unique: a unique name for this type in the brick. Only 1 protocol in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
    :type name_unique: str
    :param object_type: typing object type
    :type object_type: TypingObjectType
    :param hide: if True the typing class will not be shown to the user when retriving the typings, defaults to False
    :type hide: bool, optional
    """

    def decorator(object_class: Type[Base]):
        register_typing_class(object_class=object_class,
                              object_type=object_type, unique_name=unique_name,
                              human_name="", short_description="", hide=hide)
        return object_class
    return decorator


# Save the Typing to the TypingManager and set the _typing_name class property
def register_typing_class(
        object_class: Type[Base], object_type: TypingObjectType, unique_name: str,
        human_name: str, short_description, hide: bool = False,
        object_sub_type: str = None, related_model_typing_name: str = None) -> None:

    if not human_name:
        human_name = Utils.camel_case_to_sentence(unique_name)

    typing = Typing(
        brick=BrickHelper.get_brick_name(object_class),
        model_name=unique_name,
        model_type=object_class.full_classname(),
        object_type=object_type,
        human_name=human_name,
        short_description=short_description,
        hide=hide,
        object_sub_type=object_sub_type,
        related_model_typing_name=related_model_typing_name
    )

    TypingManager.register_typing(typing, object_class)

    object_class._typing_name = typing.typing_name
    object_class._human_name = human_name
    object_class._short_description = short_description
