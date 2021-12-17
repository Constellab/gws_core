# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import asyncio
from abc import abstractmethod
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Callable, Optional, Type, TypedDict, final

from ...brick.brick_service import BrickService
from ...config.config_types import ConfigParams, ConfigParamsDict, ConfigSpecs
from ...core.utils.logger import Logger
from ...core.utils.reflector_helper import ReflectorHelper
from ...core.utils.settings import Settings
from ...core.utils.utils import Utils
from ...impl.file.file import File
from ...impl.file.file_helper import FileHelper
from ...impl.file.file_store import FileStore
from ...impl.file.fs_node import FSNode
from ...impl.file.local_file_store import LocalFileStore
from ...io.io_spec import IOSpecsHelper
from ...resource.resource import Resource
from ...task.task import Task
from ...task.task_decorator import decorate_task, task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from ...task.task_runner import TaskRunner
from ...user.user_group import UserGroup

EXPORT_TO_PATH_META_DATA_ATTRIBUTE = '_import_from_path_meta_data'


class ExportToPathMetaData(TypedDict):
    specs: ConfigSpecs
    fs_node_type: Type[FSNode]
    inherit_specs: bool


# TODO to delete
def export_to_path(specs: ConfigSpecs = None, fs_node_type: Type[FSNode] = File,
                   inherit_specs: bool = True) -> Callable:

    def decorator(func: Callable) -> Callable:
        Logger.error('[DEPRECATED] do not use the export_to_path decorator, use only the exporter_decorator instead')
        return func

    return decorator


def exporter_decorator(
        unique_name: str, resource_type: Type[Resource],
        allowed_user: UserGroup = UserGroup.USER,
        human_name: str = None, short_description: str = None, hide: bool = False) -> Callable:
    """ Decorator to place on a ResourceExporter. It defines a special task to export a resource (of type resource_type) to
    a FsNode (file or folder)
    :param unique_name: a unique name for this task in the brick. Only 1 task in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the tasks
    :type unique_name: str
    :param resource_type: type of the resource to export to a file.
    :type resource_type: Type[Resource]
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
    :return: [description]
    :rtype: Callable
    """

    if human_name is None:
        human_name = resource_type._human_name + ' exporter'
    if short_description is None:
        short_description = f"Export {resource_type._human_name} to a file"

    def decorator(task_class: Type[ResourceExporter]):

        try:
            if not Utils.issubclass(task_class, ResourceExporter):
                raise Exception(
                    f"The exporter_decorator is used on the class: {task_class.__name__} and this class is not a sub class of ResourceExporter")

            # Check input specs
            IOSpecsHelper.check_output_specs(task_class.output_specs)
            if len(task_class.output_specs) != 1 or 'file' not in task_class.output_specs \
                    or not Utils.issubclass(task_class.output_specs['file'], FSNode):
                raise Exception(
                    f"The ResourceExporter {task_class.__name__} have invalid output specs. It must have only one input called 'file' of type FsNode (no special types)")

            # force the input specs
            task_class.input_specs = {'resource': resource_type}

            # register the task and set the human_name and short_description dynamically based on resource
            decorate_task(task_class, unique_name, human_name=human_name,
                          task_type='EXPORTER', related_resource=resource_type,
                          short_description=short_description, allowed_user=allowed_user, hide=hide)
        except Exception as err:
            BrickService.log_brick_error(task_class, str(err))

        return task_class
    return decorator


@task_decorator("ResourceExporter", hide=True)
class ResourceExporter(Task):
    """Generic task that take a file as input and return a resource

        Override the export_to_path method to export the resource into a fsNode
    """

    # The output spec can't be overrided, it will be automatically define with the correct resource type
    input_specs = {"resource": Resource}

    # /!\ The output specs can be overrided, BUT the ResourceExporter task must
    # have 1 output called file that extend FsNode (like File or Folder)
    output_specs = {"file": Resource}

    # Override the config_spec to define custom spec for the importer
    config_specs: ConfigSpecs = {}

    @final
    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:

        # Retrieve the file store
        file_store: FileStore
        if params.value_is_set('file_store_id'):
            file_store = LocalFileStore.get_by_id_and_check(params.get('file_store_id'))
        else:
            file_store = FileStore.get_default_instance()

        # Create a new temp_dir to create the file here
        self.__temp_dir: str = Settings.retrieve().make_temp_dir()

        # retrieve resource and export it to path
        resource: Resource = inputs.get('resource')
        fs_node: FSNode = await self.export_to_path(resource, self.__temp_dir, params)

        # add the node to the store
        file_store.add_node(fs_node)
        return {'file': fs_node}

    @abstractmethod
    async def export_to_path(self, resource: Resource, dest_dir: str, params: ConfigParams) -> File:
        """Override this method to generate a fs_node (File or Folder) from the resource

        :param resource: resource to export to fs_node
        :type resource: Type[Resource]
        :param dest_dir: destination directory for the fs_node
        :type dest_dir: str
        :param params: config params for the export
        :type params: ConfigParams
        :return: [description]
        :rtype: File
        """

    @final
    async def run_after_task(self) -> None:
        # delete temp dir
        FileHelper.delete_dir(self.__temp_dir)

    @final
    @classmethod
    def call(cls, resource: Resource,
             params: ConfigParamsDict = None) -> FSNode:
        """Call the ResourceExporter method manually

          :param resource: resource to export
          :type resource: Resource
          :param params: params for the import_from_path_method
          :type params: ConfigParamsDict
        """
        if not isinstance(resource, cls.get_resource_type()):
            raise Exception(f"The {cls._human_name} task required a {cls.get_resource_type()._human_name} resource")

        task_runner: TaskRunner = TaskRunner(cls, params=params, inputs={'resource': resource})

        # call the run async method in a sync function
        with ThreadPoolExecutor() as pool:
            outputs = pool.submit(asyncio.run, task_runner.run()).result()
            result = outputs['file']
            pool.submit(asyncio.run, task_runner.run_after_task())
            return result

    @final
    @classmethod
    def get_resource_type(cls) -> Type[Resource]:
        """Get the type of the resource that is exported by this task

        :return: [description]
        :rtype: Type[Resource]
        """
        return cls.input_specs['resource']
