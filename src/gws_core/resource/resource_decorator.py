

from typing import Type

from ..model.typing_register_decorator import register_typing_class
from ..resource.resource import Resource


def ResourceDecorator(name_unique: str, hide: bool = False):
    def decorator(resource_class: Type['Resource']):

        if not issubclass(resource_class, Resource):
            raise Exception(
                f"The ResourceDecorator is used on the class: {resource_class.__name} and this class is not a sub class of Resource")

        register_typing_class(object_class=resource_class,
                              object_type="RESOURCE", name_unique=name_unique, hide=hide)

        return resource_class

    return decorator
