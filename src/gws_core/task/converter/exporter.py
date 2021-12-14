

from typing import Callable, Optional, Type, TypedDict, final


from ...brick.brick_service import BrickService
from ...config.config_types import ConfigParams, ConfigSpecs
from ...config.param_spec_helper import ParamSpecHelper
from ...core.utils.decorator_helper import DecoratorHelper
from ...core.utils.reflector_helper import ReflectorHelper
from ...core.utils.settings import Settings
from ...core.utils.utils import Utils
from ...impl.file.file import File
from ...impl.file.file_helper import FileHelper
from ...impl.file.file_store import FileStore
from ...impl.file.fs_node import FSNode
from ...impl.file.local_file_store import LocalFileStore
from ...resource.resource import Resource
from ...task.task import CheckBeforeTaskResult, Task
from ...task.task_decorator import decorate_task, task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from ...user.user_group import UserGroup

EXPORT_TO_PATH_META_DATA_ATTRIBUTE = '_import_from_path_meta_data'


class ExportToPathMetaData(TypedDict):
    specs: ConfigSpecs
    fs_node_type: Type[FSNode]
    inherit_specs: bool


def export_to_path(specs: ConfigSpecs = None, fs_node_type: Type[FSNode] = File,
                   inherit_specs: bool = True) -> Callable:
    """ Decorator to place on the export_to_path method of a Resource. This works with @exporter_decorator and it allow to
        generate a Task which takes a resource as Input and generate a File. The task will call the export_to_path with the config

    :param specs: [description]
    :type specs: ConfigSpecs
    :param fs_node_type: type of the node (File or Folder) generated
    :type fs_node_type: ConfigSpecs
    :param inherit_specs: If true the specs are merge with the parent spec. If false parent specs is ignored.
    :type inherit_specs: bool
    :return: [description]
    :rtype: Callable
    """
    if specs is None:
        specs = {}

    def decorator(func: Callable) -> Callable:

        try:
            ParamSpecHelper.check_config_specs(specs)
            DecoratorHelper.check_method_decorator(func)

            # Check that the annotated method is called export_to_path
            if func.__name__ != 'export_to_path':
                raise Exception("The export_to_path decorator must be placed on a method called export_to_path")

            # Create the meta data object
            meta_data: ExportToPathMetaData = {"specs": specs,
                                               "fs_node_type": fs_node_type, "inherit_specs": inherit_specs}
            # Store the meta data object into the view_meta_data_attribute of the function
            ReflectorHelper.set_object_has_metadata(func, EXPORT_TO_PATH_META_DATA_ATTRIBUTE, meta_data)
        except Exception as err:
            BrickService.log_brick_error(func, str(err))

        return func

    return decorator


def exporter_decorator(
        unique_name: str, resource_type: Type[Resource],
        allowed_user: UserGroup = UserGroup.USER,) -> Callable:
    """ Decorator to place on a task instead of task_decorator. This decorator works with @export_to_path and it will
    generate a Task which takes a resource as Input and generate a File. This task will call the export_to_path method of the resource with the config?
    :param unique_name: a unique name for this task in the brick. Only 1 task in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the tasks
    :type unique_name: str
    :param resource_type: type of the resource to generate from the file. The resource must define the export_to_path method
    :type resource_type: Type[Resource]
    :param allowed_user: role needed to run the task. By default all user can run it. It Admin, the user need to be an admin of the lab to run the task
    :type allowed_user: ProtocolAllowedUser, optional
    :return: [description]
    :rtype: Callable
    """
    def decorator(task_class: Type[ResourceExporter]):

        try:
            if not Utils.issubclass(task_class, ResourceExporter):
                raise Exception(
                    f"The exporter_decorator is used on the class: {task_class.__name__} and this class is not a sub class of ResourceExporter")

            parent_class: Type[Task] = task_class.__base__
            if not Utils.issubclass(parent_class, Task):
                raise Exception(f"The first parent class of {task_class.__name__} must be a Task")

            meta_data: ExportToPathMetaData = get_resource_type_export_meta_data(resource_type)
            if meta_data is None:
                raise Exception(
                    f"The exporter decorator is link to resource {resource_type.classname()} but the export_to_path method of the resource is not decorated with @export_to_path decorator")

            # set the task config using the config in export to path method
            specs: ConfigSpecs = meta_data['specs']
            if meta_data['inherit_specs']:
                task_class.config_specs = {**parent_class.config_specs, **specs}
            else:
                task_class.config_specs = specs

            task_class.input_specs = {'resource': resource_type}
            task_class.output_specs = {'file': meta_data['fs_node_type']}

            # register the task and set the human_name and short_description dynamically based on resource
            decorate_task(task_class, unique_name, human_name=resource_type._human_name + ' exporter',
                          task_type='EXPORTER', related_resource=resource_type,
                          short_description=f"Export {resource_type._human_name} to a file", allowed_user=allowed_user)
        except Exception as err:
            BrickService.log_brick_error(task_class, str(err))

        return task_class
    return decorator


def get_resource_type_export_meta_data(resource_type: Type[Resource]) -> Optional[ExportToPathMetaData]:
    """ return the export_to_path metadata if the export_to_path of the resource is decorated
        return None otherwise

    :param resource_type: [description]
    :type resource_type: Type[Resource]
    :return: [description]
    :rtype: bool
    """
    return ReflectorHelper.get_and_check_object_metadata(
        resource_type.export_to_path, EXPORT_TO_PATH_META_DATA_ATTRIBUTE, dict)


@task_decorator("ResourceExporter", hide=True)
class ResourceExporter(Task):
    """Generic task that take a file as input and return a resource
    """
    input_specs = {"resource": Resource}
    output_specs = {'file': FSNode}

    @final
    def check_before_run(self, params: ConfigParams, inputs: TaskInputs) -> CheckBeforeTaskResult:
        return super().check_before_run(params, inputs)

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
        data: Resource = inputs.get('resource')
        fs_node: FSNode = data.export_to_path(self.__temp_dir, params)

        # add the node to the store
        file_store.add_node(fs_node)
        return {'file': fs_node}

    @final
    async def run_after_task(self) -> None:
        # delete temp dir
        FileHelper.delete_dir(self.__temp_dir)
