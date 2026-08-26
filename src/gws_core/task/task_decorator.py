from collections.abc import Callable
from typing import cast

from gws_core.brick.brick_log_service import BrickLogService
from gws_core.config.config_specs import ConfigSpecs
from gws_core.model.typing_deprecated import TypingDeprecated
from gws_core.model.typing_dto import TypingErrorDTO
from gws_core.model.typing_manager import TypingManager
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource import Resource

from ..core.utils.utils import Utils
from ..io.io_spec_helper import IOSpecsHelper
from ..model.typing_register_decorator import register_gws_typing_class
from ..model.typing_registration import TypingRegistration
from .task import Task
from .task_typing import TaskSubType


def task_decorator(
    unique_name: str,
    human_name: str = "",
    short_description: str = "",
    hide: bool = False,
    style: TypingStyle | None = None,
    deprecated: TypingDeprecated | None = None,
) -> Callable:
    """ Decorator to be placed on all the tasks. A task not decorated will not be runnable.
    It define static information about the task

    :param unique_name: a unique name for this task in the brick. Only 1 task in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the tasks
    :type unique_name: str
    :param human_name: optional name that will be used in the interface when viewing the tasks.
                        If not defined, the unique_name will be used
    :type human_name: str, optional
    :param short_description: optional description that will be used in the interface when viewing the tasks. Must not be longer than 255 caracters.
    :type short_description: str, optional
    :param hide: Only the task with hide=False will be available in the interface(web platform), other will be hidden.
                It is useful for task that are not meant to be viewed in the interface (like abstract classes), defaults to False
    :type hide: bool, optional
    :param style: style of the task, view TypingStyle object for more info.
                    If not provided, takes the style of the first input resource type or the first output resource type. defaults to None
    :type style: TypingStyle, optional
    :param deprecated: object to tell that the object is deprecated. See TypingDeprecated for more info, defaults to None
    :type deprecated: TypingDeprecated, optional

    """

    def decorator(task_class: type[Task]):
        decorate_task(
            task_class,
            unique_name=unique_name,
            task_type="TASK",
            human_name=human_name,
            short_description=short_description,
            hide=hide,
            style=style,
            deprecated=deprecated,
        )

        return task_class

    return decorator


def _check_task_specs(task_class: type[Task]) -> list[TypingErrorDTO] | None:
    """Check and normalize the input, output and config specs of a task class.

    Definition errors are collected (not raised): the task is still registered, but marked
    as errored so it appears as broken and can't run.

    :param task_class: task class being decorated
    :type task_class: type[Task]
    :return: the list of definition errors (possibly empty), or None if the specs could not be
             checked at all, meaning the task must not be registered
    :rtype: list[TypingErrorDTO] | None
    """
    definition_errors: list[TypingErrorDTO] = []

    try:
        task_class.input_specs = IOSpecsHelper.check_input_specs(task_class.input_specs, task_class)
        task_class.output_specs = IOSpecsHelper.check_output_specs(
            task_class.output_specs, task_class
        )

        # IOSpecs construction never raises on an invalid spec; it records the
        # problem instead. Register the task anyway, marked as errored.
        if not task_class.input_specs.is_valid:
            BrickLogService.log_brick_error(
                task_class,
                f"Invalid input specs for task {task_class.__name__}: "
                f"{task_class.input_specs.invalid_reason}",
            )
            definition_errors.append(
                TypingErrorDTO(
                    source="input", message=cast(str, task_class.input_specs.invalid_reason)
                )
            )
        if not task_class.output_specs.is_valid:
            BrickLogService.log_brick_error(
                task_class,
                f"Invalid output specs for task {task_class.__name__}: "
                f"{task_class.output_specs.invalid_reason}",
            )
            definition_errors.append(
                TypingErrorDTO(
                    source="output", message=cast(str, task_class.output_specs.invalid_reason)
                )
            )

        # check the config specs
        if isinstance(task_class.config_specs, dict):
            # TODO for now this is just a warning
            BrickLogService.log_brick_warning(
                task_class,
                f"The config specs of task {task_class.__name__} must be an ConfigSpecs object and not a dict. The dict support will be removed in the future",
            )

            task_class.config_specs = ConfigSpecs(task_class.config_specs)

        # ConfigSpecs construction never raises on an invalid param key; it
        # records the problem instead. Register the task anyway, marked as
        # errored, so a single bad config doesn't break the brick load.
        if not task_class.config_specs.is_valid:
            BrickLogService.log_brick_error(
                task_class,
                f"Invalid config specs for task {task_class.__name__}: "
                f"{task_class.config_specs.invalid_reason}",
            )
            definition_errors.append(
                TypingErrorDTO(
                    source="config", message=cast(str, task_class.config_specs.invalid_reason)
                )
            )
        else:
            task_class.config_specs.check_config_specs()

    except Exception as err:
        BrickLogService.log_brick_error(
            task_class, f"Invalid specs for the task : {task_class.__name__}. {str(err)}"
        )
        return None

    return definition_errors


def decorate_task(
    task_class: type[Task],
    unique_name: str,
    task_type: TaskSubType,
    related_resource: type[Resource] | None = None,
    human_name: str = "",
    short_description: str = "",
    hide: bool = False,
    style: TypingStyle | None = None,
    deprecated: TypingDeprecated | None = None,
):
    """Method to decorate a task"""
    if not Utils.issubclass(task_class, Task):
        BrickLogService.log_brick_error(
            task_class,
            f"The task_decorator is used on the class: {task_class.__name__} and this class is not a sub class of Task",
        )
        return

    if related_resource and not Utils.issubclass(related_resource, Resource):
        BrickLogService.log_brick_error(
            task_class, f"The task {unique_name} has a related object which is not a resource."
        )
        return

    if not Utils.value_is_in_literal(task_type, TaskSubType):
        BrickLogService.log_brick_error(
            task_class,
            f"The task_type '{task_type}' for the task is invalid: {task_class.__name__}. Available values: {Utils.get_literal_values(TaskSubType)}",
        )
        return

    # Definition errors are collected (not raised): the task is still
    # registered, but marked as errored so it appears as broken and can't run.
    # Check the input, output and config specs
    definition_errors = _check_task_specs(task_class)
    if definition_errors is None:
        return

    # Set the default style if not defined
    if not style:
        style = get_task_default_style(task_class)
    elif not style.background_color or not style.icon_color:
        style.copy_from_style(get_task_default_style(task_class))

    related_resource_typing_name = related_resource.get_typing_name() if related_resource else None

    register_gws_typing_class(
        TypingRegistration(
            object_class=task_class,
            object_type="TASK",
            unique_name=unique_name,
            object_sub_type=task_type,
            human_name=human_name,
            short_description=short_description,
            hide=hide,
            style=style,
            related_model_typing_name=related_resource_typing_name,
            deprecated=deprecated,
            definition_errors=definition_errors or None,
        )
    )


def get_task_default_style(task_class: type[Task]) -> TypingStyle:
    """Get the default style for a task, use the first input style or the first output style"""
    default_typing_name = None
    # only derive a style from a valid spec: an invalid IOSpec may carry a
    # None / non-resource type, so get_default_resource_type() is not usable
    first_input = (
        task_class.input_specs.get_first_spec() if task_class.input_specs.is_valid else None
    )
    if first_input:
        default_typing_name = first_input.get_default_resource_type().get_typing_name()
    else:
        first_output = (
            task_class.output_specs.get_first_spec()
            if task_class.output_specs.is_valid
            else None
        )
        if first_output:
            default_typing_name = first_output.get_default_resource_type().get_typing_name()

    if default_typing_name:
        typing = TypingManager.get_typing_from_name(default_typing_name)
        if typing and typing.style:
            return typing.style

    return TypingStyle.default_task()
