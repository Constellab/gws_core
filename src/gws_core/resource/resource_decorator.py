# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Callable, List, Type

from ..model.typing_register_decorator import register_typing_class
from ..resource.resource import Resource


def resource_decorator(unique_name: str, human_name: str = "", short_description: str = "",
                       serializable_fields: List[str] = None, model: type = None, hide: bool = False) -> Callable:
    """ Decorator to be placed on all the resourcees. A resource not decorated will not be runnable.
    It define static information about the resource

    :param name_unique: a unique name for this resource in the brick. Only 1 resource in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the resourcees
    :type name_unique: str
    :param human_name: optional name that will be used in the interface when viewing the resourcees. Must not be longer than 20 caracters
                        If not defined, the name_unique will be used
    :type human_name: str, optional
    :param short_description: optional description that will be used in the interface when viewing the resourcees. Must not be longer than 100 caracters
    :type short_description: str, optional
    :param serializable_fields: optional List of field to automatically serialize/deserialise on the resource
    :type serializable_fields: str, optional
    :param model: optional ResourceModel type
    :type model: type, optional
    :param hide: Only the resource will hide=False will be available in the interface, other will be hidden.
                It is useful for resource that are not meant to be viewed in the interface (like abstract classes), defaults to False
    :type hide: bool, optional

    """

    def decorator(resource_class: Type[Resource]):
        if not issubclass(resource_class, Resource):
            raise Exception(
                f"The ResourceDecorator is used on class '{resource_class.__name__}' while this class is not a subclass of Resource")

        register_typing_class(object_class=resource_class, object_type="RESOURCE", unique_name=unique_name,
                              human_name=human_name, short_description=short_description, hide=hide)

        if serializable_fields and isinstance(serializable_fields, list):
            # pylint: disable=protected-access
            # save the fields to ignore in _serializable_fields class proprty
            if resource_class._serializable_fields is None:
                resource_class._serializable_fields = serializable_fields
            else:
                # for child classes, append the serializable field from parent fields
                resource_class._serializable_fields = serializable_fields + resource_class._serializable_fields

        from .resource_model import ResourceModel
        if model:
            if issubclass(model, ResourceModel):
                # pylint: disable=protected-access
                resource_class._resource_model_type = model
            else:
                raise BaseException("In valid resource_decorator argument. Argument 'model' must be a subclass of ResourceModel")

        return resource_class

    return decorator
