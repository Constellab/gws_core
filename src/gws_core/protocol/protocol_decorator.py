# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Callable, Type

from gws_core.model.typing_deprecated import TypingDeprecated
from gws_core.model.typing_style import TypingStyle

from ..brick.brick_service import BrickService
from ..core.utils.utils import Utils
from ..model.typing_register_decorator import register_gws_typing_class
from ..protocol.protocol import Protocol


def protocol_decorator(unique_name: str,
                       human_name: str = "",
                       short_description: str = "",
                       hide: bool = False,
                       style: TypingStyle = None,
                       deprecated_since: str = None,
                       deprecated_message: str = None,
                       deprecated: TypingDeprecated = None) -> Callable:
    """ Decorator to be placed on all the protocols. A protocol not decorated will not be runnable.
    It define static information about the protocol

    :param unique_name: a unique name for this protocol in the brick. Only 1 protocol in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the protocols
    :type unique_name: str
    :param human_name: optional name that will be used in the interface when viewing the protocols.
                        If not defined, the unique_name will be used
    :type human_name: str, optional
    :param short_description: optional description that will be used in the interface when viewing the protocols. Must not be longer than 255 caracters.
    :type short_description: str, optional
    :param style: style of the task, view TypingStyle object for more info, defaults to None
    :type style: TypingStyle, optional
    :param hide: Only the protocol will hide=False will be available in the interface, other will be hidden.
                It is useful for protocol that are not meant to be viewed in the interface (like abstract classes), defaults to False
    :type hide: bool, optional
    :param deprecated: object to tell that the object is deprecated. See TypingDeprecated for more info, defaults to None
    :type deprecated: TypingDeprecated, optional

    """
    # provide the style default value
    if style is None:
        style = TypingStyle.default_protocol()

    def decorator(protocol_class: Type[Protocol]):
        if not Utils.issubclass(protocol_class, Protocol):
            BrickService.log_brick_error(
                protocol_class,
                f"The ProtocolDecorator is used on the class: {protocol_class.__name__} and this class is not a sub class of Protocol")
            return protocol_class

        register_gws_typing_class(object_class=protocol_class,
                                  object_type="PROTOCOL",
                                  unique_name=unique_name,
                                  object_sub_type='PROTOCOL',
                                  human_name=human_name,
                                  short_description=short_description,
                                  hide=hide,
                                  style=style,
                                  deprecated_since=deprecated_since,
                                  deprecated_message=deprecated_message,
                                  deprecated=deprecated)

        return protocol_class
    return decorator
