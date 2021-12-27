# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import asyncio
from abc import abstractmethod
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Type, final

from ...brick.brick_service import BrickService
from ...config.config_types import ConfigParams, ConfigParamsDict, ConfigSpecs
from ...core.utils.utils import Utils
from ...resource.resource import Resource
from ...task.task import Task
from ...task.task_decorator import decorate_task, task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from ...task.task_runner import TaskRunner
from ...task.task_typing import TaskSubType
from ...user.user_group import UserGroup


def decorate_converter(task_class: Type['Converter'], unique_name: str, task_type: TaskSubType,
                       source_type: Type[Resource] = Resource, target_type: Type[Resource] = Resource,
                       related_resource: Type[Resource] = None,
                       allowed_user: UserGroup = UserGroup.USER,
                       human_name: str = "", short_description: str = "", hide: bool = False) -> None:
    if not Utils.issubclass(task_class, Converter):
        BrickService.log_brick_error(
            task_class,
            f"The decorate_converter is used on the class: {task_class.__name__} and this class is not a sub class of Converter")
        return

    # force the input and output specs
    task_class.input_specs = {'source': source_type}
    task_class.output_specs = {'target': target_type}

    # register the task and set the human_name and short_description dynamically based on resource
    decorate_task(task_class, unique_name, human_name=human_name, related_resource=related_resource,
                  task_type=task_type, short_description=short_description, allowed_user=allowed_user, hide=hide)


@task_decorator("Converter", hide=True)
class Converter(Task):
    input_specs = {"source": Resource}
    output_specs = {"target": Resource}

    # Override the config_spec to define custom spec for the importer
    config_specs: ConfigSpecs = {}

    @final
    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # retrieve resource
        resource: Resource = inputs.get('source')

        # call convert method
        target: Resource = await self.convert(resource, params, self.get_target_type())

        return {'target': target}

    @abstractmethod
    async def convert(self, source: Resource, params: ConfigParams, target_type: Type[Resource]) -> Resource:
        """ Override this method to implement convert method

        :param resource: [description]
        :type resource: Resource
        :param params: [description]
        :type params: ConfigParams
        :param target_type: [description]
        :type target_type: Type[Resource]
        :return: [description]
        :rtype: Resource
        """

    @final
    @classmethod
    def call(cls, source: Resource,
             params: ConfigParamsDict = None) -> Resource:
        """Call the ResourceExporter method manually

          :param resource: resource to export
          :type resource: Resource
          :param params: params for the import_from_path_method
          :type params: ConfigParamsDict
        """
        if not isinstance(source, cls.get_source_type()):
            raise Exception(f"The {cls.__name__} task requires a {cls.get_source_type().__name__} resource")

        task_runner: TaskRunner = TaskRunner(cls, params=params, inputs={'source': source})

        # call the run async method in a sync function
        with ThreadPoolExecutor() as pool:
            outputs = pool.submit(asyncio.run, task_runner.run()).result()
            result = outputs['target']
            pool.submit(asyncio.run, task_runner.run_after_task())
            return result

    @final
    @classmethod
    def get_source_type(cls) -> Type[Resource]:
        """Get the type of the input source

        :return: [description]
        :rtype: Type[Resource]
        """
        return cls.input_specs['source']

    @final
    @classmethod
    def get_target_type(cls) -> Type[Resource]:
        """Get the type of the output target

        :return: [description]
        :rtype: Type[Resource]
        """
        return cls.output_specs['target']
