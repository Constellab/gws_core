from typing import Callable, Type

from ..brick.brick_service import BrickService
from ..core.utils.utils import Utils
from ..model.typing_register_decorator import register_gws_typing_class
from ..protocol.protocol import Protocol
from ..user.user_group import UserGroup


def protocol_decorator(unique_name: str, allowed_user: UserGroup = UserGroup.USER,
                       human_name: str = "", short_description: str = "", hide: bool = False,
                       icon: str = None,
                       deprecated_since: str = None, deprecated_message: str = None) -> Callable:
    """ Decorator to be placed on all the protocols. A protocol not decorated will not be runnable.
    It define static information about the protocol

    :param unique_name: a unique name for this protocol in the brick. Only 1 protocol in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the protocols
    :type unique_name: str
    :param allowed_user: role needed to run the protocol. By default all user can run it. It Admin, the user need to be an admin of the lab to run the protocol
    :type allowed_user: ProtocolAllowedUser, optional
    :param human_name: optional name that will be used in the interface when viewing the protocols. Must not be longer than 20 caracters
                        If not defined, the unique_name will be used
    :type human_name: str, optional
    :param short_description: optional description that will be used in the interface when viewing the protocols. Must not be longer than 100 caracters
    :type short_description: str, optional
    :param hide: Only the protocol will hide=False will be available in the interface, other will be hidden.
                It is useful for protocol that are not meant to be viewed in the interface (like abstract classes), defaults to False
    :type hide: bool, optional
    :param icon: icon to display in the interface when viewing the protocols.
                Select icon name from : https://fonts.google.com/icons?icon.set=Material+Icons, defaults to None
    :type icon: str, optional
    :param deprecated_since: To provide when the object is deprecated. It must be a version string like 1.0.0 to
                            tell at which version the object became deprecated, defaults to None
    :type deprecated_since: str, optional
    :param deprecated_message: Active when deprecated_since is provided. It describe a message about the deprecation.
                For example you can provide the name of another object to use instead, defaults to None
    :type deprecated_message: str, optional

    """
    def decorator(protocol_class: Type[Protocol]):
        if not Utils.issubclass(protocol_class, Protocol):
            BrickService.log_brick_error(
                protocol_class,
                f"The ProtocolDecorator is used on the class: {protocol_class.__name__} and this class is not a sub class of Protocol")
            return protocol_class

        register_gws_typing_class(object_class=protocol_class, object_type="PROTOCOL", unique_name=unique_name,
                                  object_sub_type='PROTOCOL',
                                  human_name=human_name, short_description=short_description, hide=hide,
                                  icon=icon,
                                  deprecated_since=deprecated_since, deprecated_message=deprecated_message)

        # set the allowed user for the protocol
        protocol_class._allowed_user = allowed_user

        return protocol_class
    return decorator
