# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import asyncio
from abc import abstractmethod
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Callable, Type, Union, final

from ...brick.brick_service import BrickService
from ...config.config_types import ConfigParams, ConfigParamsDict, ConfigSpecs
from ...core.utils.utils import Utils
from ...impl.file.file import File
from ...impl.file.fs_node import FSNode
from ...io.io_spec import IOSpecsHelper
from ...resource.resource import Resource
from ...task.task import Task
from ...task.task_decorator import decorate_task, task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from ...task.task_runner import TaskRunner
from ...user.user_group import UserGroup


def importer_decorator(
        unique_name: str, resource_type: Type[Resource],
        allowed_user: UserGroup = UserGroup.USER,
        human_name: str = None, short_description: str = None, hide: bool = False) -> Callable:
    """ Decorator to place on a ResourceImporter instead of task_decorator. It defines a special task to import a FsNode (file or folder)
    to resource_type
    :param unique_name: a unique name for this task in the brick. Only 1 task in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the tasks
    :type unique_name: str
    :param resource_type: type of the resource to generate from the file.
    :type resource_type: ProtocolAllowedUser, optional
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
        human_name = resource_type._human_name + ' importer'
    if short_description is None:
        short_description = f"Import file to {resource_type._human_name}"

    def decorator(task_class: Type[ResourceImporter]):

        try:
            if not Utils.issubclass(task_class, ResourceImporter):
                raise Exception(
                    f"The importer_decorator is used on the class: {task_class.__name__} and this class is not a sub class of ResourceImporter")

            # Check input specs
            IOSpecsHelper.check_input_specs(task_class.input_specs)
            if len(task_class.input_specs) != 1 or 'source' not in task_class.input_specs \
                    or not Utils.issubclass(task_class.input_specs['source'], FSNode):
                raise Exception(
                    f"The ResourceImporter {task_class.__name__} have invalid input specs. It must have only one input called 'source' of type FsNode (no special types)")

            # force the output specs
            task_class.output_specs = {'target': resource_type}

            # register the task
            decorate_task(task_class, unique_name, human_name=human_name,
                          task_type='IMPORTER', related_resource=resource_type,
                          short_description=short_description, allowed_user=allowed_user, hide=hide)
        except Exception as err:
            BrickService.log_brick_error(task_class, str(err))

        return task_class
    return decorator


@task_decorator("ResourceImporter", hide=True)
class ResourceImporter(Task):
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
    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        fs_node: FSNode = inputs.get('source')
        resource: Resource = await self.import_from_path(fs_node, params, self.get_target_type())
        return {'target': resource}

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

    @final
    @classmethod
    def call(cls, fs_node: Union[FSNode, str],
             params: ConfigParamsDict = None) -> Resource:
        """Call the ResourceImporter method manually

          :param fs_node: provide a FsNode or a string. If a string, it create a File with the string as path
          :type fs_node: Union[FSNode, str]
          :param params: params for the import_from_path_method
          :type params: ConfigParamsDict
        """
        fs_node_obj: FSNode
        if isinstance(fs_node, FSNode):
            fs_node_obj = fs_node
        else:
            fs_node_obj = File(fs_node)

        task_runner: TaskRunner = TaskRunner(cls, params=params, inputs={'source': fs_node_obj})

        # call the run async method in a sync function
        with ThreadPoolExecutor() as pool:
            outputs = pool.submit(asyncio.run, task_runner.run()).result()
            result = outputs['target']
            pool.submit(asyncio.run, task_runner.run_after_task())
            return result

    @final
    @classmethod
    def get_target_type(cls) -> Type[Resource]:
        """Get the type of the resource that is imported by this task

        :return: [description]
        :rtype: Type[Resource]
        """
        return cls.output_specs['target']
