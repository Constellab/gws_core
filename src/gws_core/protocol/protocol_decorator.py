from typing import Type

from ..model.typing_register_decorator import register_typing_class
from .protocol import Protocol


def ProtocolDecorator(unique_name: str, hide: bool = False):
    def decorator(protocol_class: Type[Protocol]):
        if not issubclass(protocol_class, Protocol):
            raise Exception(
                f"The ProtocolDecorator is used on the class: {protocol_class.__name} and this class is not a sub class of Protocol")

        register_typing_class(object_class=protocol_class,
                              object_type="PROTOCOL", unique_name=unique_name, hide=hide)

        return protocol_class
    return decorator
