

from abc import abstractmethod
from typing import Callable, Type, final

from ...brick.brick_service import BrickService
from ...config.config_types import ConfigParams, ConfigSpecs
from ...core.utils.utils import Utils
from ...impl.file.fs_node import FSNode
from ...io.io_spec import IOSpecsHelper
from ...resource.resource import Resource
from ...task.task import Task
from ...task.task_decorator import decorate_task, task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from ...user.user_group import UserGroup


def importer_decorator(
        unique_name: str, resource_type: Type[Resource],
        allowed_user: UserGroup = UserGroup.USER) -> Callable:
    """ Decorator to place on a ResourceImporter instead of task_decorator. This decorator works with @import_from_path and it will generate a Task
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
    def decorator(task_class: Type[ResourceImporter]):

        try:
            if not Utils.issubclass(task_class, ResourceImporter):
                raise Exception(
                    f"The importer_decorator is used on the class: {task_class.__name__} and this class is not a sub class of ResourceImporter")

            IOSpecsHelper.check_input_specs(task_class.input_specs)

            if len(task_class.input_specs) != 1 or 'file' not in task_class.input_specs \
                    or not Utils.issubclass(task_class.input_specs['file'], FSNode):
                raise Exception(
                    f"The ResourceImporter {task_class.__name__} have invalid input specs. It must have only one input called 'file' of type file (no special types)")

            # force the output specs
            task_class.output_specs = {'resource': resource_type}

            # set resource type in ResourceImporter
            task_class._resource_type = resource_type

            # register the task and set the human_name and short_description dynamically based on resource
            decorate_task(task_class, unique_name, human_name=resource_type._human_name + ' importer',
                          task_type='IMPORTER', related_resource=resource_type,
                          short_description=f"Import file to {resource_type._human_name}", allowed_user=allowed_user)
        except Exception as err:
            BrickService.log_brick_error(task_class, str(err))

        return task_class
    return decorator


@task_decorator("ResourceImporter", hide=True)
class ResourceImporter(Task):
    """Generic task that take a file as input and return a resource

    Override the import_from_path method to import the file to the destination resource
    """

    # /!\ The input specs can be override, BUT the RessourceImporter task must
    # have 1 input called file that extend FsNode (like File or Folder)
    input_specs = {'file': FSNode}

    # The output spec can't be overrided, it will be automatically define with the correct resource type
    output_specs = {"resource": Resource}

    # Override the config_spec to define custom spec for the importer
    config_specs: ConfigSpecs = {}

    # Do not modify, this is provided by the importer_decorator
    _resource_type: Type[Resource]

    @final
    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        fs_node: FSNode = inputs.get('file')
        resource: Resource = await self.import_from_path(fs_node, params, self.output_specs['resource'])
        return {'resource': resource}

    @abstractmethod
    async def import_from_path(self, fs_node: FSNode, params: ConfigParams, destination_type: Type[Resource]) -> Resource:
        """Override the import form path method to create the destination resource from the file

        :param fs_node: file resource to import
        :type fs_node: FSNode
        :param params: config params
        :type params: ConfigParams
        :param destination_type: resource type of the result. Useful to make generic importers
        :type destination_type: Type[Resource]
        :return: resource of type destination_type
        :rtype: Resource
        """
