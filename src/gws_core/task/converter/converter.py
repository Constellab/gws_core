

from abc import abstractmethod
from typing import Tuple, Type, final

from gws_core.config.config_params import ConfigParamsDict
from gws_core.config.config_specs import ConfigSpecs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_deprecated import TypingDeprecated
from gws_core.model.typing_manager import TypingManager
from gws_core.model.typing_style import TypingStyle

from ...brick.brick_service import BrickService
from ...config.config_params import ConfigParams
from ...core.utils.utils import Utils
from ...resource.resource import Resource
from ...task.task import CheckBeforeTaskResult, Task
from ...task.task_decorator import decorate_task, task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from ...task.task_runner import TaskRunner
from ...task.task_typing import TaskSubType


def decorate_converter(task_class: Type['Converter'],
                       unique_name: str,
                       task_type: TaskSubType,
                       source_type: Type[Resource] = Resource,
                       target_type: Type[Resource] = Resource,
                       related_resource: Type[Resource] = None,
                       human_name: str = "",
                       short_description: str = "",
                       hide: bool = False,
                       style: TypingStyle = None,
                       output_sub_class: bool = False,
                       deprecated_since: str = None,
                       deprecated_message: str = None,
                       deprecated: TypingDeprecated = None) -> None:
    if not Utils.issubclass(task_class, Converter):
        BrickService.log_brick_error(
            task_class,
            f"The decorate_converter is used on the class: {task_class.__name__} and this class is not a sub class of Converter")
        return

    if not Utils.issubclass(source_type, Resource):
        BrickService.log_brick_error(
            task_class,
            f"The source_type: {source_type.__name__} is not a sub class of Resource")
        return

    # force the input and output specs
    task_class.input_specs = InputSpecs(
        {Converter.input_name: InputSpec(source_type)})
    task_class.output_specs = OutputSpecs(
        {Converter.output_name: OutputSpec(target_type, sub_class=output_sub_class)})

    main_resource_type = target_type if task_type == 'IMPORTER' else source_type
    if not style:
        # for the importer, takes the destination type
        style = get_converter_default_style(main_resource_type)
    elif not style.background_color or not style.icon_color:
        style.copy_from_style(get_converter_default_style(main_resource_type))

    # register the task and set the human_name and short_description dynamically based on resource
    decorate_task(task_class=task_class,
                  unique_name=unique_name,
                  human_name=human_name,
                  related_resource=related_resource,
                  task_type=task_type,
                  short_description=short_description,
                  hide=hide,
                  style=style,
                  deprecated_since=deprecated_since,
                  deprecated_message=deprecated_message,
                  deprecated=deprecated)


def get_converter_default_style(resource_type: Type[Resource]) -> TypingStyle:
    """Get the default style for a task, use the first input style or the first output style
    """

    typing = TypingManager.get_typing_from_name(resource_type.get_typing_name())
    if typing and typing.style:
        return typing.style

    return TypingStyle.default_task()


@task_decorator("Converter", hide=True)
class Converter(Task):
    # name of the input and output for converter
    input_name: str = 'source'
    output_name: str = 'target'

    input_specs = InputSpecs({"source": InputSpec(Resource)})
    output_specs = OutputSpecs({"target": OutputSpec(Resource)})

    # Override the config_spec to define custom spec for the importer
    config_specs = ConfigSpecs({})

    @final
    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # retrieve resource
        resource: Resource = inputs.get(Converter.input_name)

        # call convert method
        target: Resource = self.convert(
            resource, params, self.get_target_type())

        if target is None:
            raise Exception('The target resource is None')

        return {Converter.output_name: target}

    @abstractmethod
    def convert(self, source: Resource, params: ConfigParams, target_type: Type[Resource]) -> Resource:
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
            raise Exception(
                f"The {cls.__name__} task requires a {cls.get_source_type()[0].__name__} resource")

        converter_runner: ConverterRunner = ConverterRunner(
            cls, params=params, input_=source)

        result = converter_runner.run()
        return result

    @final
    @classmethod
    def get_source_type(cls) -> Tuple[Type[Resource]]:
        """Get the type of the input source

        :return: [description]
        :rtype: Type[Resource]
        """
        return cls.input_specs.get_spec(Converter.input_name).get_resource_type_tuples()

    @final
    @classmethod
    def get_target_type(cls) -> Type[Resource]:
        """Get the type of the output target

        :return: [description]
        :rtype: Type[Resource]
        """
        return cls.output_specs.get_spec(Converter.output_name).get_default_resource_type()


class ConverterRunner():
    """Class to run a converter

    :raises Exception: [description]
    :return: [description]
    :rtype: [type]
    """

    _task_runner: TaskRunner

    def __init__(self, converter_type: Type[Converter], params: ConfigParamsDict = None,
                 input_: Resource = None) -> None:
        if not Utils.issubclass(converter_type, Converter):
            raise Exception('The ConverterRunner must have a Converter')

        self._task_runner = TaskRunner(converter_type, params)

        if input_ is not None:
            self.set_input(input_)

    def check_before_run(self) -> CheckBeforeTaskResult:
        return self._task_runner.check_before_run()

    def run(self) -> Resource:
        self._task_runner.run()
        return self.get_output()

    def run_after_task(self) -> None:
        self._task_runner.run_after_task()

    def set_input(self, resource: Resource) -> None:
        self._task_runner.set_input(Converter.input_name, resource)

    def get_output(self) -> Resource:
        return self._task_runner.get_output(Converter.output_name)
