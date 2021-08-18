from enum import Enum
from typing import Callable, Type

from gws_core.protocol.protocol import Protocol

from ..model.typing_register_decorator import register_typing_class
from ..process.process_model import ProcessAllowedUser
from .protocol_model import ProtocolModel


def ProtocolDecorator(unique_name: str, allowed_user: ProcessAllowedUser = ProcessAllowedUser.ALL,
                      human_name: str = "", short_description: str = "", hide: bool = False) -> Callable:
    """ Decorator to be placed on all the protocols. A protocol not decorated will not be runnable.
    It define static information about the protocol

    :param name_unique: a unique name for this protocol in the brick. Only 1 protocol in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the protocols
    :type name_unique: str
    :param allowed_user: role needed to run the protocol. By default all user can run it. It Admin, the user need to be an admin of the lab to run the protocol
    :type allowed_user: ProtocolAllowedUser, optional
    :param human_name: optional name that will be used in the interface when viewing the protocols. Must not be longer than 20 caracters
                        If not defined, the name_unique will be used
    :type human_name: str, optional
    :param short_description: optional description that will be used in the interface when viewing the protocols. Must not be longer than 100 caracters
    :type short_description: str, optional
    :param hide: Only the protocol will hide=False will be available in the interface, other will be hidden.
                It is useful for protocol that are not meant to be viewed in the interface (like abstract classes), defaults to False
    :type hide: bool, optional

    """
    def decorator(protocol_class: Type[Protocol]):
        if not issubclass(protocol_class, Protocol):
            raise Exception(
                f"The ProtocolDecorator is used on the class: {protocol_class.__name__} and this class is not a sub class of Protocol")

        register_typing_class(object_class=protocol_class, object_type="PROTOCOL", unique_name=unique_name,
                              human_name=human_name, short_description=short_description, hide=hide)

        # set the allowed user for the protocol
        protocol_class._allowed_user = allowed_user

        return protocol_class
    return decorator
