# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Callable, Type

from ...brick.brick_service import BrickService
from ...core.utils.utils import Utils
from ...model.typing_register_decorator import register_typing_class
from ...task.converter.importer import ResourceImporter, importer_decorator
from .file import File


def importable_resource_decorator(
        unique_name: str, resource_importer: Type[ResourceImporter],
        human_name: str = "", short_description: str = "", hide: bool = False) -> Callable:
    """ Decorator to be placed on importable resource (link files). This resource is linked to another resource
    to import the file into the resource type

    :param unique_name: a unique name for this resource in the brick. Only 1 resource in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the resourcees
    :type unique_name: str
    :param import_destination: type of the resource used when importing this resource
    :type import_destination: Type[Resource]
    :param human_name: optional name that will be used in the interface when viewing the resourcees. Must not be longer than 20 caracters
                        If not defined, the unique_name will be used
    :type human_name: str, optional
    :param short_description: optional description that will be used in the interface when viewing the resourcees. Must not be longer than 100 caracters
    :type short_description: str, optional
    :param hide: Only the resource will hide=False will be available in the interface, other will be hidden.
                It is useful for resource that are not meant to be viewed in the interface (like abstract classes), defaults to False
    :type hide: bool, optional

    """
    def decorator(resource_class: Type[File]):
        if not Utils.issubclass(resource_class, File):
            BrickService.log_brick_error(
                resource_class,
                f"The importable resource '{resource_class.__name__}' is not a subclass of File")
            return resource_class

        if not Utils.issubclass(resource_importer, ResourceImporter):
            BrickService.log_brick_error(
                resource_class,
                f"The importable resource '{resource_class.__name__}' use the resource importer '{resource_class.__name__}' but this class is not a subclass of ResourceImporter")
            return resource_class

        register_typing_class(resource_class, object_type="RESOURCE", unique_name=unique_name, human_name=human_name,
                              short_description=short_description, hide=hide,
                              object_sub_type='IMPORTABLE_RESOURCE')

        # save the importer decorator in the file type
        resource_class._resource_importer = resource_importer
        return resource_class

    return decorator
