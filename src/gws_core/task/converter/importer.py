# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import traceback
from abc import abstractmethod
from typing import Callable, List, Type, final

from gws_core.impl.file.file import File
from gws_core.impl.file.file_helper import FileHelper
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_style import TypingStyle

from ...brick.brick_service import BrickService
from ...config.config_params import ConfigParams
from ...config.config_types import ConfigSpecs
from ...core.utils.utils import Utils
from ...impl.file.fs_node import FSNode
from ...resource.resource import Resource
from ...user.user_group import UserGroup
from ..task_decorator import task_decorator
from .converter import Converter, decorate_converter


def importer_decorator(
        unique_name: str, target_type: Type[Resource], supported_extensions: List[str],
        source_type: Type[FSNode] = File,
        allowed_user: UserGroup = UserGroup.USER, human_name: str = None,
        short_description: bool = None, hide: bool = False,
        style: TypingStyle = None,
        deprecated_since: str = None, deprecated_message: str = None) -> Callable:
    """ Decorator to place on a ResourceImporter instead of task_decorator. It defines a special task to import a FsNode (file or folder)
    to resource_type
    :param unique_name: a unique name for this task in the brick. Only 1 task in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the tasks
    :type unique_name: str
    :param target_type: Type of the resource output after the import
    :type target_type: ProtocolAllowedUser, optional
    :param supported_extensions: List of supported extension of file input supported by the importer
    :type supported_extensions: List[str], optional
    :param source_type: If provided, the importer works only on subclasses of source_type
    :type source_type: Type[FSNode], optional
    :param allowed_user: role needed to run the task. By default all user can run it. It Admin, the user need to be an admin of the lab to run the task
    :type allowed_user: ProtocolAllowedUser, optional
    :param human_name: optional name that will be used in the interface when viewing the tasks. Must not be longer than 20 caracters
                        If not defined, an automatic is generated.
    :type human_name: str, optional
    :param short_description: optional description that will be used in the interface when viewing the tasks. Must not be longer than 100 caracters
                              If not defined, an automatic is generated
    :type short_description: str, optional
    :param hide: Only the task with hide=False will be available in the interface(web platform), other will be hidden.
                It is useful for task that are not meant to be viewed in the interface (like abstract classes), defaults to False
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

            task_class._supported_extensions = supported_extensions
            human_name_computed = human_name or target_type._human_name + ' importer'
            short_description_computed = short_description or f"Import file to {target_type._human_name}"

            # register the task
            decorate_converter(
                task_class, unique_name=unique_name, task_type='IMPORTER', source_type=source_type,
                target_type=target_type, related_resource=source_type, human_name=human_name_computed,
                short_description=short_description_computed, allowed_user=allowed_user, hide=hide, style=style,
                deprecated_since=deprecated_since, deprecated_message=deprecated_message)
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
    input_specs = InputSpecs({'source': InputSpec(FSNode)})

    # The output spec can't be overrided, it will be automatically define with the correct resource type
    output_specs = OutputSpecs({"target": OutputSpec(Resource)})

    # Override the config_spec to define custom spec for the importer
    config_specs: ConfigSpecs = {}

    _supported_extensions: List[str] = []

    @final
    def convert(self, source: FSNode, params: ConfigParams, target_type: Type[Resource]) -> Resource:

        if not source.path:
            raise Exception("Cannot import the file because the path is not defined.")

        if not source.exists():
            raise Exception(f"Cannot import file '{source.name or source.path}' because it doesn't exists.")

        try:
            target: Resource = self.import_from_path(source, params, target_type)
        except Exception as err:
            raise Exception(
                f"Cannot import file '{source.path}' using importer : '{self._typing_name}' because of the following error: {err}")

        if target.name is None:
            # set the target name = FsNode name without extension
            target.name = FileHelper.get_name(source.path)
        return target

    @abstractmethod
    def import_from_path(self, source: FSNode, params: ConfigParams, target_type: Type[Resource]) -> Resource:
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
