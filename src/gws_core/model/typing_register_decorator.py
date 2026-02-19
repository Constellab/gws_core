from collections.abc import Callable

from gws_core.core.model.base import Base
from gws_core.core.model.base_typing import BaseTyping
from gws_core.core.utils.string_helper import StringHelper
from gws_core.core.utils.utils import Utils
from gws_core.model.typing_deprecated import TypingDeprecated
from gws_core.model.typing_style import TypingStyle

from ..brick.brick_helper import BrickHelper
from ..brick.brick_log_service import BrickLogService
from ..model.typing import Typing
from ..model.typing_dto import TypingObjectType
from .typing_manager import TypingManager


def typing_registrator(
    unique_name: str,
    object_type: TypingObjectType,
    hide: bool = False,
    style: TypingStyle | None = None,
) -> Callable:
    """Decorator to register the class as a typing with a typing name

    param name_unique: a unique name for this type in the brick. Only 1 protocol in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
    :type name_unique: str
    :param object_type: typing object type
    :type object_type: TypingObjectType
    :param hide: if True the typing class will not be shown to the user when retriving the typings, defaults to False
    :type hide: bool, optional
    """

    def decorator(object_class: type[Base]):
        register_typing_class(
            object_class=object_class,
            object_type=object_type,
            unique_name=unique_name,
            human_name="",
            short_description="",
            hide=hide,
            style=style,
        )
        return object_class

    return decorator


# Save the Typing to the TypingManager and set the typing_name class property
def register_typing_class(
    object_class: type[Base],
    object_type: TypingObjectType,
    unique_name: str,
    human_name: str,
    short_description,
    hide: bool = False,
    style: TypingStyle | None = None,
    object_sub_type: str | None = None,
    related_model_typing_name: str | None = None,
    deprecated: TypingDeprecated | None = None,
) -> None:
    if not human_name:
        human_name = StringHelper.camel_case_to_sentence(unique_name)

    # check deprecated_since version
    if deprecated is not None and not deprecated.check_version():
        # import the BrickLogService here and not in register_typing_class because it would create a cyclic error
        BrickLogService.log_brick_error(
            object_class,
            f"The deprecated_since property '{deprecated.deprecated_since}' for typing object {human_name} is not a version. Must be formatted like 1.0.0",
        )
        deprecated = None

    if not Utils.value_is_in_literal(object_type, TypingObjectType):
        BrickLogService.log_brick_error(
            object_class,
            f"The type {object_type} is not authorized in Typing, possible values: {Utils.get_literal_values(TypingObjectType)}",
        )
        return

    typing = Typing(
        brick=BrickHelper.get_brick_name(object_class),
        brick_version=None,  # set to None because the version is not loaded yet
        unique_name=unique_name,
        model_type=object_class.full_classname(),
        object_type=object_type,
        human_name=human_name,
        short_description=short_description,
        hide=hide,
        style=style,
        object_sub_type=object_sub_type,
        related_model_typing_name=related_model_typing_name,
        deprecated_since=deprecated.deprecated_since if deprecated else None,
        deprecated_message=deprecated.deprecated_message if deprecated else None,
    )

    TypingManager.register_typing(typing, object_class)

    if issubclass(object_class, BaseTyping):
        object_class.__set_typing_name__(typing.typing_name)
        object_class.__set_human_name__(human_name)
        object_class.__set_short_description__(short_description)
        object_class.__set_style__(style)


# Method to register gws object like Resource, Task and Protocol
def register_gws_typing_class(
    object_class: type[Base],
    object_type: TypingObjectType,
    unique_name: str,
    human_name: str,
    short_description,
    hide: bool = False,
    style: TypingStyle | None = None,
    object_sub_type: str | None = None,
    related_model_typing_name: str | None = None,
    deprecated: TypingDeprecated | None = None,
) -> None:
    # import the BrickLogService here and not in register_typing_class because it would create a cyclic error

    # check if unique name is only alpha numeric and '_'
    if not unique_name or not StringHelper.is_alphanumeric(unique_name):
        BrickLogService.log_brick_error(
            object_class,
            f"The unique name '{unique_name}' for typing object {human_name} is not valid. It must contains only alpha numeric characters and '_'.",
        )
        return

    # provide the style default value
    if style is None:
        style = TypingStyle.default_task()
    else:
        style.fill_empty_values()

    register_typing_class(
        object_class=object_class,
        object_type=object_type,
        unique_name=unique_name,
        human_name=human_name,
        short_description=short_description,
        hide=hide,
        style=style,
        object_sub_type=object_sub_type,
        related_model_typing_name=related_model_typing_name,
        deprecated=deprecated,
    )
