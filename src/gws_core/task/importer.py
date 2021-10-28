

from inspect import isclass
from typing import Callable, Type, TypedDict, final

from ..config.config_types import ConfigParams, ConfigSpecs
from ..config.param_spec_helper import ParamSpecHelper
from ..core.utils.decorator_helper import DecoratorHelper
from ..core.utils.reflector_helper import ReflectorHelper
from ..impl.file.file import File
from ..impl.file.fs_node import FSNode
from ..resource.resource import Resource
from ..task.task import CheckBeforeTaskResult, Task
from ..task.task_decorator import decorate_task, task_decorator
from ..task.task_io import TaskInputs, TaskOutputs
from ..user.user_group import UserGroup

IMPORT_FROM_PATH_META_DATA_ATTRIBUTE = '__import_from_path_mata_data'


class ImportFromPathMetaData(TypedDict):
    specs: ConfigSpecs
    fs_node_type: Type[FSNode]


def import_from_path(specs: ConfigSpecs = None, fs_node_type: Type[FSNode] = File) -> Callable:
    """ Decorator to place on the import_from_path method of a Resource. This works with @importer_decorator and it allow to
        generate a Task which takes a file as Input and return the resource. The task will call the import_from_path with the config

    :param specs: [description]
    :type specs: ConfigSpecs
    :param fs_node_type: Type of the node (file of folder) required to import the path
    :type fs_node_type: ConfigSpecs
    :return: [description]
    :rtype: Callable
    """
    if specs is None:
        specs = {}

    ParamSpecHelper.check_config_specs(specs)

    def decorator(func: Callable) -> Callable:

        DecoratorHelper.check_method_decorator(func)

        # Check that the annotated method is called import_from_path
        if func.__name__ != 'import_from_path':
            raise Exception("The import_from_path decorator must be placed on a method called import_from_path")

        # Create the meta data object
        meta_data: ImportFromPathMetaData = {"specs": specs, "fs_node_type": fs_node_type}
        # Store the meta data object into the view_meta_data_attribute of the function
        ReflectorHelper.set_object_has_metadata(func, IMPORT_FROM_PATH_META_DATA_ATTRIBUTE, meta_data)

        return func

    return decorator


def importer_decorator(
        unique_name: str, resource_type: Type[Resource],
        allowed_user: UserGroup = UserGroup.USER) -> Callable:
    """ Decorator to place on a TaskImporter instead of task_decorator. This decorator works with @import_from_path and it will generate a Task
    which takes a file as Input and return the resource of type resource_type. This task will call the import_from_path method of the resource with the config.
    :param unique_name: a unique name for this task in the brick. Only 1 task in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the tasks
    :type unique_name: str
    :param resource_type: type of the resource to generate from the file. The resource must define the import_from_path method
    :type resource_type: ProtocolAllowedUser, optional
    :param allowed_user: role needed to run the task. By default all user can run it. It Admin, the user need to be an admin of the lab to run the task
    :type allowed_user: ProtocolAllowedUser, optional
    :return: [description]
    :rtype: Callable
    """
    def decorator(task_class: Type[TaskImporter]):

        if not isclass(task_class) or not issubclass(task_class, TaskImporter):
            raise Exception(
                f"The importer_decorator is used on the class: {task_class.__name__} and this class is not a sub class of TaskImporter")

        meta_data: ImportFromPathMetaData = ReflectorHelper.get_and_check_object_metadata(
            resource_type.import_from_path, IMPORT_FROM_PATH_META_DATA_ATTRIBUTE, dict)
        if meta_data is None:
            raise Exception(
                f"The importer decorator is link to resource {resource_type.classname()} but the import_from_path method of the resource is not decoated with @import_from_path decorator")

        # set the task config using the config in import_from_path method
        task_class.config_specs = meta_data['specs']

        task_class.input_specs = {'file': meta_data['fs_node_type']}
        task_class.output_specs = {'data': resource_type}

        # set resource type in task
        task_class.__resource_type = resource_type

        # register the task and set the human_name and short_description dynamically based on resource
        decorate_task(task_class, unique_name, human_name=resource_type._human_name + ' importer',
                      short_description=f"Import file to {resource_type._human_name}", allowed_user=allowed_user)

        return task_class
    return decorator


@task_decorator("TaskImporter", hide=True)
class TaskImporter(Task):
    """Generic task that take a file as input and return a resource
    """
    input_specs = {'fs_node': FSNode}
    output_specs = {"data": Resource}

    # Do not modify, this is provided by the importer_decorator
    __resource_type: Type[Resource]

    @final
    def check_before_run(self, params: ConfigParams, inputs: TaskInputs) -> CheckBeforeTaskResult:
        return super().check_before_run(params, inputs)

    @final
    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        fs_node: FSNode = inputs.get('file')
        resource: Resource = self.__resource_type.import_from_path(fs_node, params)
        return {'data': resource}

    @final
    async def run_after_task(self) -> None:
        pass
