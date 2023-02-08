# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import traceback
from abc import abstractmethod
from typing import Callable, Type, TypedDict, final

from gws_core.io.io_spec import InputSpec, OutputSpec

from ...brick.brick_service import BrickService
from ...config.config_types import ConfigParams, ConfigSpecs
from ...core.utils.settings import Settings
from ...core.utils.utils import Utils
from ...impl.file.file import File
from ...impl.file.fs_node import FSNode
from ...resource.resource import Resource
from ...task.task_decorator import task_decorator
from ...user.user_group import UserGroup
from .converter import Converter, decorate_converter

EXPORT_TO_PATH_META_DATA_ATTRIBUTE = '_import_from_path_meta_data'


class ExportToPathMetaData(TypedDict):
    specs: ConfigSpecs
    fs_node_type: Type[FSNode]
    inherit_specs: bool


def exporter_decorator(
        unique_name: str, source_type: Type[Resource], target_type: Type[FSNode] = File,
        allowed_user: UserGroup = UserGroup.USER,
        human_name: str = None, short_description: str = None, hide: bool = False,
        deprecated_since: str = None, deprecated_message: str = None) -> Callable:
    """ Decorator to place on a ResourceExporter. It defines a special task to export a resource (of type resource_type) to
    a FsNode (file or folder)
    :param unique_name: a unique name for this task in the brick. Only 1 task in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the tasks
    :type unique_name: str
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
    :param deprecated_since: To provide when the object is deprecated. It must be a version string like 1.0.0 to
                            tell at which version the object became deprecated, defaults to None
    :type deprecated_since: str, optional
    :param deprecated_message: Active when deprecated_since is provided. It describe a message about the deprecation.
                For example you can provide the name of another object to use instead, defaults to None
    :type deprecated_message: str, optional
    :return: [description]
    :rtype: Callable
    """

    def decorator(task_class: Type[ResourceExporter]):

        try:
            if not Utils.issubclass(task_class, ResourceExporter):
                BrickService.log_brick_error(
                    task_class,
                    f"The exporter_decorator is used on the class: {task_class.__name__} and this class is not a sub class of ResourceExporter")
                return task_class

            if not Utils.issubclass(target_type, FSNode):
                BrickService.log_brick_error(
                    task_class,
                    f"Error in the exporter_decorator of class {task_class.__name__}. The target_type must be an FsNode or child class")
                return task_class

            human_name_computed = human_name or source_type._human_name + ' exporter'
            short_description_computed = short_description or f"Export {source_type._human_name} to a file"

            # mark the resource as exportable
            source_type._is_exportable = True

            # register the task
            decorate_converter(
                task_class, unique_name=unique_name, task_type='EXPORTER', source_type=source_type,
                target_type=target_type, related_resource=source_type, human_name=human_name_computed,
                short_description=short_description_computed, allowed_user=allowed_user, hide=hide,
                deprecated_since=deprecated_since, deprecated_message=deprecated_message)
        except Exception as err:
            traceback.print_stack()
            BrickService.log_brick_error(task_class, str(err))

        return task_class
    return decorator


@task_decorator("ResourceExporter", hide=True)
class ResourceExporter(Converter):
    """Generic task that take a file as input and return a resource

        Override the export_to_path method to export the resource into a fsNode
    """

    # The output spec can't be overrided, it will be automatically define with the correct resource type
    input_specs = {"source": InputSpec(Resource)}

    # /!\ The output specs can be overrided, BUT the ResourceExporter task must
    # have 1 output called file that extend FsNode (like File or Folder)
    output_specs = {"target": OutputSpec(FSNode)}

    # Override the config_spec to define custom spec for the exporter
    config_specs: ConfigSpecs = {}

    @final
    async def convert(self, source: Resource, params: ConfigParams, target_type: Type[Resource]) -> FSNode:
        # Create a new temp_dir to create the file here
        self.__temp_dir: str = Settings.get_instance().make_temp_dir()

        try:
            fs_node: FSNode = await self.export_to_path(source, self.__temp_dir, params, target_type)
        except Exception as err:
            raise Exception(
                f"Cannot export the resource '{source.name}' using exporter '{self._typing_name}' to a file, error : {err}")

        return fs_node

    @abstractmethod
    async def export_to_path(self, source: Resource, dest_dir: str, params: ConfigParams, target_type: Type[FSNode]) -> FSNode:
        """Override this method to generate a fs_node (File or Folder) from the resource

        :param resource: resource to export to fs_node
        :type resource: Type[Resource]
        :param dest_dir: destination directory for the fs_node
        :type dest_dir: str
        :param params: config params for the export
        :type params: ConfigParams
        :param target_type: file type of the result, defined in output_specs. Useful to make generic exporter
        :type params: Type[FSNode]
        :return: resource of type target_type
        :rtype: File
        """
