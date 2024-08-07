

from typing import Callable, Type

from gws_core.core.utils.reflector_helper import ReflectorHelper
from gws_core.model.typing_deprecated import TypingDeprecated
from gws_core.model.typing_manager import TypingManager
from gws_core.model.typing_style import TypingStyle

from ..brick.brick_service import BrickService
from ..core.utils.utils import Utils
from ..model.typing_register_decorator import register_gws_typing_class
from ..resource.resource import Resource


def resource_decorator(unique_name: str,
                       human_name: str = "",
                       short_description: str = "",
                       hide: bool = False,
                       style: TypingStyle = None,
                       deprecated_since: str = None,
                       deprecated_message: str = None,
                       deprecated: TypingDeprecated = None) -> Callable:
    """ Decorator to be placed on all the resourcees. A resource not decorated will not be runnable.
    It define static information about the resource

    :param unique_name: a unique name for this resource in the brick. Only 1 resource in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the resourcees
    :type unique_name: str
    :param human_name: optional name that will be used in the interface when viewing the resources.
                        If not defined, the unique_name will be used
    :type human_name: str, optional
    :param short_description: optional description that will be used in the interface when viewing the resourcees. Must not be longer than 255 caracters.
    :type short_description: str, optional
    :param hide: Only the resource will hide=False will be available in the interface, other will be hidden.
                It is useful for resource that are not meant to be viewed in the interface (like abstract classes), defaults to False
    :type hide: bool, optional
    :param style: style of the task, view TypingStyle object for more info, defaults to None
    :type style: TypingStyle, optional
    :param deprecated: object to tell that the object is deprecated. See TypingDeprecated for more info, defaults to None
    :type deprecated: TypingDeprecated, optional

    """

    def decorator(resource_class: Type[Resource]):
        decorate_resource(resource_class,
                          unique_name=unique_name,
                          human_name=human_name,
                          short_description=short_description,
                          hide=hide,
                          style=style,
                          deprecated_since=deprecated_since,
                          deprecated_message=deprecated_message,
                          deprecated=deprecated)

        return resource_class

    return decorator


def decorate_resource(resource_class: Type[Resource],
                      unique_name: str,
                      human_name: str = "",
                      short_description: str = "",
                      hide: bool = False,
                      style: TypingStyle = None,
                      deprecated_since: str = None,
                      deprecated_message: str = None,
                      deprecated: TypingDeprecated = None):
    """Method to decorate a resource
    """
    if not Utils.issubclass(resource_class, Resource):
        BrickService.log_brick_error(
            resource_class,
            f"The ResourceDecorator is used on class '{resource_class.__name__}' but this class is not a subclass of Resource")
        return resource_class

    # check resource constructor, it must have only optional params
    if not ReflectorHelper.function_args_are_optional(resource_class.__init__):
        BrickService.log_brick_error(
            resource_class,
            f"The Resource '{resource_class.__name__}' have a constructor with mandatory params. The resource constructor must contain only optional arguments")
        return resource_class

    if not style:
        style = get_resource_default_style(resource_class)
    elif not style.background_color or not style.icon_color:
        style.copy_from_style(get_resource_default_style(resource_class))

    register_gws_typing_class(object_class=resource_class,
                              object_type="RESOURCE",
                              unique_name=unique_name,
                              human_name=human_name,
                              short_description=short_description,
                              hide=hide,
                              style=style,
                              object_sub_type='RESOURCE',
                              deprecated_since=deprecated_since,
                              deprecated_message=deprecated_message,
                              deprecated=deprecated)


def get_resource_default_style(resource_class: Type[Resource]) -> TypingStyle:
    """Get the default style for a resource
    """
    # get parent class
    parent_class: Type[Resource] = resource_class.__bases__[0]

    if not parent_class or not issubclass(parent_class, Resource):
        return TypingStyle.default_resource()

    parent_typing = TypingManager.get_typing_from_name(parent_class.get_typing_name())
    if parent_typing and parent_typing.style:
        return parent_typing.style
    return TypingStyle.default_resource()
