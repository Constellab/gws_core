from abc import abstractmethod
from dataclasses import dataclass
from typing import final

from gws_core.brick.brick_log_service import BrickLogService
from gws_core.config.config_params import ConfigParamsDict
from gws_core.config.config_specs import ConfigSpecs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_deprecated import TypingDeprecated
from gws_core.model.typing_manager import TypingManager
from gws_core.model.typing_style import TypingStyle

from ...config.config_params import ConfigParams
from ...core.utils.utils import Utils
from ...resource.resource import Resource
from ...task.task import CheckBeforeTaskResult, Task
from ...task.task_decorator import decorate_task, task_decorator
from ...task.task_io import TaskInputs, TaskOutputs
from ...task.task_runner import TaskRunner
from ...task.task_typing import TaskSubType


@dataclass
class ConverterRegistration:
    """Description of a converter (importer, exporter, transformer...) to register.

    These values travel together from the converter decorators down to decorate_task,
    so they are grouped in a single object instead of being forwarded one by one.

    :param task_class: converter class to register
    :type task_class: type[Converter]
    :param unique_name: a unique name for this task in the brick. Only 1 task in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
    :type unique_name: str
    :param task_type: sub type of the converter task (IMPORTER, EXPORTER, TRANSFORMER...)
    :type task_type: TaskSubType
    :param source_type: type of the resource taken as input, defaults to Resource
    :type source_type: type[Resource]
    :param target_type: type of the resource returned as output, defaults to Resource
    :type target_type: type[Resource]
    :param related_resource: resource this converter is related to, defaults to None
    :type related_resource: type[Resource] | None
    :param human_name: name used in the interface. If empty, it is generated from the unique_name
    :type human_name: str
    :param short_description: description used in the interface. Must not be longer than 255 caracters
    :type short_description: str
    :param hide: Only the task with hide=False will be available in the interface, other will be hidden, defaults to False
    :type hide: bool
    :param style: style of the task. If not provided, takes the style of the main resource type, defaults to None
    :type style: TypingStyle | None
    :param output_sub_class: if True, the output supports sub classes of target_type, defaults to False
    :type output_sub_class: bool
    :param deprecated: object to tell that the object is deprecated. See TypingDeprecated for more info, defaults to None
    :type deprecated: TypingDeprecated | None
    """

    task_class: type["Converter"]
    unique_name: str
    task_type: TaskSubType
    source_type: type[Resource] = Resource
    target_type: type[Resource] = Resource
    related_resource: type[Resource] | None = None
    human_name: str = ""
    short_description: str = ""
    hide: bool = False
    style: TypingStyle | None = None
    output_sub_class: bool = False
    deprecated: TypingDeprecated | None = None


def decorate_converter(registration: ConverterRegistration) -> None:
    """Register a converter from its description.

    :param registration: description of the converter to register
    :type registration: ConverterRegistration
    """
    task_class = registration.task_class
    source_type = registration.source_type
    target_type = registration.target_type

    if not Utils.issubclass(task_class, Converter):
        BrickLogService.log_brick_error(
            task_class,
            f"The decorate_converter is used on the class: {task_class.__name__} and this class is not a sub class of Converter",
        )
        return

    if not Utils.issubclass(source_type, Resource):
        BrickLogService.log_brick_error(
            task_class, f"The source_type: {source_type.__name__} is not a sub class of Resource"
        )
        return

    # force the input and output specs
    task_class.input_specs = InputSpecs({Converter.input_name: InputSpec(source_type)})
    task_class.output_specs = OutputSpecs(
        {
            Converter.output_name: OutputSpec(
                target_type, sub_class=registration.output_sub_class
            )
        }
    )

    main_resource_type = target_type if registration.task_type == "IMPORTER" else source_type
    style = registration.style
    if not style:
        # for the importer, takes the destination type
        style = get_converter_default_style(main_resource_type)
    elif not style.background_color or not style.icon_color:
        style.copy_from_style(get_converter_default_style(main_resource_type))

    # register the task and set the human_name and short_description dynamically based on resource
    decorate_task(
        task_class=task_class,
        unique_name=registration.unique_name,
        human_name=registration.human_name,
        related_resource=registration.related_resource,
        task_type=registration.task_type,
        short_description=registration.short_description,
        hide=registration.hide,
        style=style,
        deprecated=registration.deprecated,
    )


def get_converter_default_style(resource_type: type[Resource]) -> TypingStyle:
    """Get the default style for a task, use the first input style or the first output style"""

    typing = TypingManager.get_typing_from_name(resource_type.get_typing_name())
    if typing and typing.style:
        return typing.style

    return TypingStyle.default_task()


@task_decorator("Converter", hide=True)
class Converter(Task):
    # name of the input and output for converter
    input_name: str = "source"
    output_name: str = "target"

    input_specs = InputSpecs({"source": InputSpec(Resource)})
    output_specs = OutputSpecs({"target": OutputSpec(Resource)})

    # Override the config_spec to define custom spec for the importer
    config_specs = ConfigSpecs({})

    @final
    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # retrieve resource
        resource: Resource = inputs.get(Converter.input_name)

        # call convert method
        target: Resource = self.convert(resource, params, self.get_target_type())

        if target is None:
            raise Exception("The target resource is None")

        return {Converter.output_name: target}

    @abstractmethod
    def convert(
        self, source: Resource, params: ConfigParams, target_type: type[Resource]
    ) -> Resource:
        """Override this method to implement convert method

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
    def call(cls, source: Resource, params: ConfigParamsDict | None = None) -> Resource:
        """Call the ResourceExporter method manually

        :param resource: resource to export
        :type resource: Resource
        :param params: params for the import_from_path_method
        :type params: ConfigParamsDict
        """
        if not isinstance(source, cls.get_source_type()):
            raise Exception(
                f"The {cls.__name__} task requires a {cls.get_source_type()[0].__name__} resource"
            )

        converter_runner: ConverterRunner = ConverterRunner(cls, params=params, input_=source)

        result = converter_runner.run()
        return result

    @final
    @classmethod
    def get_source_type(cls) -> tuple[type[Resource]]:
        """Get the type of the input source

        :return: [description]
        :rtype: Type[Resource]
        """
        return cls.input_specs.get_spec(Converter.input_name).get_resource_type_tuples()

    @final
    @classmethod
    def get_target_type(cls) -> type[Resource]:
        """Get the type of the output target

        :return: [description]
        :rtype: Type[Resource]
        """
        return cls.output_specs.get_spec(Converter.output_name).get_default_resource_type()


class ConverterRunner:
    """Class to run a converter

    :raises Exception: [description]
    :return: [description]
    :rtype: [type]
    """

    _task_runner: TaskRunner

    def __init__(
        self,
        converter_type: type[Converter],
        params: ConfigParamsDict | None = None,
        input_: Resource | None = None,
    ) -> None:
        if not Utils.issubclass(converter_type, Converter):
            raise Exception("The ConverterRunner must have a Converter")

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
