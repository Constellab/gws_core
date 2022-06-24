# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import asyncio
from abc import abstractmethod
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Tuple, Type, final

from gws_core.io.io_spec import InputSpec, OutputSpec

from ...brick.brick_service import BrickService
from ...config.config_types import ConfigParams, ConfigParamsDict, ConfigSpecs
from ...core.utils.utils import Utils
from ...resource.resource import Resource
from ...task.task import CheckBeforeTaskResult, Task
from ...task.task_decorator import decorate_task, task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from ...task.task_runner import TaskRunner
from ...task.task_typing import TaskSubType
from ...user.user_group import UserGroup


def decorate_converter(task_class: Type['Converter'], unique_name: str, task_type: TaskSubType,
                       source_type: Type[Resource] = Resource, target_type: Type[Resource] = Resource,
                       related_resource: Type[Resource] = None,
                       allowed_user: UserGroup = UserGroup.USER,
                       human_name: str = "", short_description: str = "", hide: bool = False,
                       deprecated_since: str = None, deprecated_message: str = None) -> None:
    if not Utils.issubclass(task_class, Converter):
        BrickService.log_brick_error(
            task_class,
            f"The decorate_converter is used on the class: {task_class.__name__} and this class is not a sub class of Converter")
        return

    # force the input and output specs
    task_class.input_specs = {Converter.input_name: InputSpec(source_type)}
    task_class.output_specs = {Converter.output_name: OutputSpec(target_type)}

    # register the task and set the human_name and short_description dynamically based on resource
    decorate_task(task_class, unique_name, human_name=human_name, related_resource=related_resource,
                  task_type=task_type, short_description=short_description, allowed_user=allowed_user, hide=hide,
                  deprecated_since=deprecated_since, deprecated_message=deprecated_message)


@task_decorator("Converter", hide=True)
class Converter(Task):
    # name of the input and output for converter
    input_name: str = 'source'
    output_name: str = 'target'

    input_specs = {"source": InputSpec(Resource)}
    output_specs = {"target": OutputSpec(Resource)}

    # Override the config_spec to define custom spec for the importer
    config_specs: ConfigSpecs = {}

    @final
    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # retrieve resource
        resource: Resource = inputs.get(Converter.input_name)

        # call convert method
        target: Resource = await self.convert(resource, params, self.get_target_type())

        if target is None:
            raise Exception('The target resource is None')

        if target.name is None:
            # set the target name source name
            target.name = resource.name

        return {Converter.output_name: target}

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

        converter_runner: ConverterRunner = ConverterRunner(cls, params=params, input=source)

        # call the run async method in a sync function
        with ThreadPoolExecutor() as pool:
            result = pool.submit(asyncio.run, converter_runner.run()).result()
            pool.submit(asyncio.run, converter_runner.run_after_task())
            return result

    @final
    @classmethod
    def get_source_type(cls) -> Tuple[Type[Resource]]:
        """Get the type of the input source

        :return: [description]
        :rtype: Type[Resource]
        """
        return cls.input_specs[Converter.input_name].get_resource_type_tuples()

    @final
    @classmethod
    def get_target_type(cls) -> Type[Resource]:
        """Get the type of the output target

        :return: [description]
        :rtype: Type[Resource]
        """
        return cls.output_specs[Converter.output_name].get_default_resource_type()


class ConverterRunner():
    """Class to run a converter

    :raises Exception: [description]
    :return: [description]
    :rtype: [type]
    """

    _task_runner: TaskRunner

    def __init__(self, converter_type: Type[Converter], params: ConfigParamsDict = None,
                 input: Resource = None) -> None:
        if not Utils.issubclass(converter_type, Converter):
            raise Exception('The ConverterRunner must have a Converter')

        self._task_runner = TaskRunner(converter_type, params)

        if input is not None:
            self.set_input(input)

    def check_before_run(self) -> CheckBeforeTaskResult:
        self._task_runner.check_before_run()

    async def run(self) -> Resource:
        await self._task_runner.run()
        return self.get_output()

    async def run_after_task(self) -> None:
        await self._task_runner.run_after_task()

    def set_input(self, resource: Resource) -> None:
        self._task_runner.set_input(Converter.input_name, resource)

    def get_output(self) -> Resource:
        return self._task_runner.get_output(Converter.output_name)
