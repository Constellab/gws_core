# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import traceback
from abc import abstractmethod
from typing import Callable, Type, final

from gws_core.impl.file.file import File

from ...brick.brick_service import BrickService
from ...config.config_types import ConfigParams, ConfigSpecs
from ...core.utils.utils import Utils
from ...impl.file.fs_node import FSNode
from ...resource.resource import Resource
from ...user.user_group import UserGroup
from ..task_decorator import task_decorator
from .converter import Converter, decorate_converter


def importer_decorator(
        unique_name: str, target_type: Type[Resource], source_type: Type[FSNode] = File,
        allowed_user: UserGroup = UserGroup.USER, human_name: str = None,
        short_description: bool = None, hide: bool = False) -> Callable:
    """ Decorator to place on a ResourceImporter instead of task_decorator. It defines a special task to import a FsNode (file or folder)
    to resource_type
    :param unique_name: a unique name for this task in the brick. Only 1 task in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the tasks
    :type unique_name: str
    :param allowed_user: role needed to run the task. By default all user can run it. It Admin, the user need to be an admin of the lab to run the task
    :type allowed_user: ProtocolAllowedUser, optional
    :param human_name: optional name that will be used in the interface when viewing the tasks. Must not be longer than 20 caracters
    :param human_name: optional name that will be used in the interface when viewing the tasks. Must not be longer than 20 caracters
                        If not defined, an automatic is generated.
    :type human_name: str, optional
    :param short_description: optional description that will be used in the interface when viewing the tasks. Must not be longer than 100 caracters
                              If not defined, an automatic is generated
    :type short_description: str, optional
    :param hide: Only the task with hide=False will be available in the interface(web platform), other will be hidden.
                It is useful for task that are not meant to be viewed in the interface (like abstract classes), defaults to False
    :type hide: bool, optional
    :return: [description]
    :rtype: Callable
    """
    def decorator(task_class: Type[ResourceImporter]):
        try:
            if not Utils.issubclass(task_class, ResourceImporter):
                BrickService.log_brick_error(
                    task_class,
                    f"The importer_decorator is used on the class: {task_class.__name__} and this class is not a sub class of ResourceImporter")
                return task_class

            if not Utils.issubclass(source_type, FSNode):
                BrickService.log_brick_error(
                    task_class,
                    f"Error in the importer_decorator of class {task_class.__name__}. The source_type must be an FsNode or child class")
                return task_class

            human_name_computed = human_name or target_type._human_name + ' importer'
            short_description_computed = short_description or f"Import file to {target_type._human_name}"

            # mark the resource as importable
            source_type._is_importable = True

            # register the task
            decorate_converter(task_class, unique_name=unique_name, task_type='IMPORTER',
                               source_type=FSNode, target_type=target_type, related_resource=source_type,
                               human_name=human_name_computed, short_description=short_description_computed,
                               allowed_user=allowed_user, hide=hide)
        except Exception as err:
            traceback.print_stack()
            BrickService.log_brick_error(task_class, str(err))

        return task_class
    return decorator


@task_decorator("ResourceImporter", hide=True)
class ResourceImporter(Converter):
    """Generic task that take a file as input and return a resource

    Override the import_from_path method to import the file to the destination resource
    """

    # /!\ The input specs can be overrided, BUT the RessourceImporter task must
    # have 1 input called source that extend FsNode (like File or Folder)
    input_specs = {'source': FSNode}

    # The output spec can't be overrided, it will be automatically define with the correct resource type
    output_specs = {"target": Resource}

    # Override the config_spec to define custom spec for the importer
    config_specs: ConfigSpecs = {}

    @final
    async def convert(self, source: FSNode, params: ConfigParams, target_type: Type[Resource]) -> Resource:
        return await self.import_from_path(source, params, target_type)

    @abstractmethod
    async def import_from_path(self, source: FSNode, params: ConfigParams, target_type: Type[Resource]) -> Resource:
        """Override the import form path method to create the destination resource from the file

        :param fs_node: file resource to import
        :type fs_node: FSNode
        :param params: config params
        :type params: ConfigParams
        :param target_type: resource type of the result, defined in input_specs. Useful to make generic importers
        :type target_type: Type[Resource]
        :return: resource of type target_type
        :rtype: Resource
        """
