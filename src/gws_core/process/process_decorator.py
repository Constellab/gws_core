

from typing import Type

from ..model.typing_register_decorator import register_typing_class
from .process import Process


def ProcessDecorator(name_unique: str, hide: bool = False):
    def decorator(process_class: Type[Process]):
        if not issubclass(process_class, Process):
            raise Exception(
                f"The ProcessDecorator is used on the class: {process_class.__name} and this class is not a sub class of Process")

        register_typing_class(object_class=process_class,
                              object_type="PROCESS", name_unique=name_unique, hide=hide)

        return process_class
    return decorator
