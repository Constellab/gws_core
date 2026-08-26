from collections.abc import Callable

from gws_core.core.model.base import Base
from gws_core.core.model.base_typing import BaseTyping
from gws_core.core.utils.string_helper import StringHelper
from gws_core.core.utils.utils import Utils
from gws_core.model.typing_registration import TypingRegistration
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
            TypingRegistration(
                object_class=object_class,
                object_type=object_type,
                unique_name=unique_name,
                hide=hide,
                style=style,
            )
        )
        return object_class

    return decorator


# Save the Typing to the TypingManager and set the typing_name class property
def register_typing_class(registration: TypingRegistration) -> None:
    """Register a typing from its description.

    :param registration: description of the typing to register
    :type registration: TypingRegistration
    """
    object_class = registration.object_class
    human_name = registration.human_name or StringHelper.camel_case_to_sentence(
        registration.unique_name
    )
    deprecated = registration.deprecated

    # check deprecated_since version
    if deprecated is not None and not deprecated.check_version():
        # import the BrickLogService here and not in register_typing_class because it would create a cyclic error
        BrickLogService.log_brick_error(
            object_class,
            f"The deprecated_since property '{deprecated.deprecated_since}' for typing object {human_name} is not a version. Must be formatted like 1.0.0",
        )
        deprecated = None

    if not Utils.value_is_in_literal(registration.object_type, TypingObjectType):
        BrickLogService.log_brick_error(
            object_class,
            f"The type {registration.object_type} is not authorized in Typing, possible values: {Utils.get_literal_values(TypingObjectType)}",
        )
        return

    definition_errors = registration.definition_errors

    typing = Typing(
        brick=BrickHelper.get_brick_name(object_class),
        brick_version=None,  # set to None because the version is not loaded yet
        unique_name=registration.unique_name,
        model_type=object_class.full_classname(),
        object_type=registration.object_type,
        human_name=human_name,
        short_description=registration.short_description,
        hide=registration.hide,
        style=registration.style,
        object_sub_type=registration.object_sub_type,
        related_model_typing_name=registration.related_model_typing_name,
        deprecated_since=deprecated.deprecated_since if deprecated else None,
        deprecated_message=deprecated.deprecated_message if deprecated else None,
        definition_errors=(
            [error.to_json_dict() for error in definition_errors] if definition_errors else None
        ),
    )

    TypingManager.register_typing(typing, object_class)

    if issubclass(object_class, BaseTyping):
        object_class.__set_typing_name__(typing.typing_name)
        object_class.__set_human_name__(human_name)
        object_class.__set_short_description__(registration.short_description)
        if registration.style is not None:
            object_class.__set_style__(registration.style)


# Method to register gws object like Resource, Task and Protocol
def register_gws_typing_class(registration: TypingRegistration) -> None:
    """Register a typing of a gws object (Resource, Task, Protocol...). It checks the unique name
    and provides a default style before delegating to register_typing_class.

    :param registration: description of the typing to register
    :type registration: TypingRegistration
    """
    # import the BrickLogService here and not in register_typing_class because it would create a cyclic error

    # check if unique name is only alpha numeric and '_'
    if not registration.unique_name or not StringHelper.is_alphanumeric(registration.unique_name):
        BrickLogService.log_brick_error(
            registration.object_class,
            f"The unique name '{registration.unique_name}' for typing object {registration.human_name} is not valid. It must contains only alpha numeric characters and '_'.",
        )
        return

    # provide the style default value
    if registration.style is None:
        registration.style = TypingStyle.default_task()
    else:
        registration.style.fill_empty_values()

    register_typing_class(registration)
