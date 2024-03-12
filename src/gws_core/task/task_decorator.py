# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Callable, Type

from gws_core.model.typing_deprecated import TypingDeprecated
from gws_core.model.typing_manager import TypingManager
from gws_core.model.typing_style import TypingStyle
from gws_core.resource.resource import Resource

from ..brick.brick_service import BrickService
from ..config.param.param_spec_helper import ParamSpecHelper
from ..core.utils.utils import Utils
from ..io.io_spec_helper import IOSpecsHelper
from ..model.typing_register_decorator import register_gws_typing_class
from .task import Task
from .task_typing import TaskSubType


def task_decorator(unique_name: str,
                   human_name: str = "",
                   short_description: str = "",
                   hide: bool = False,
                   style: TypingStyle = None,
                   deprecated_since: str = None,
                   deprecated_message: str = None,
                   deprecated: TypingDeprecated = None) -> Callable:
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
    def decorator(task_class: Type[Task]):
        decorate_task(task_class,
                      unique_name=unique_name,
                      task_type='TASK',
                      human_name=human_name,
                      short_description=short_description,
                      hide=hide,
                      style=style,
                      deprecated_since=deprecated_since,
                      deprecated_message=deprecated_message,
                      deprecated=deprecated)

        return task_class
    return decorator


def decorate_task(
        task_class: Type[Task],
        unique_name: str,
        task_type: TaskSubType,
        related_resource: Type[Resource] = None,
        human_name: str = "",
        short_description: str = "",
        hide: bool = False,
        style: TypingStyle = None,
        deprecated_since: str = None,
        deprecated_message: str = None,
        deprecated: TypingDeprecated = None):
    """Method to decorate a task
    """
    if not Utils.issubclass(task_class, Task):
        BrickService.log_brick_error(
            task_class,
            f"The task_decorator is used on the class: {task_class.__name__} and this class is not a sub class of Task")
        return

    if related_resource and not Utils.issubclass(related_resource, Resource):
        BrickService.log_brick_error(
            task_class,
            f"The task {unique_name} has a related object which is not a resource.")
        return

    if not Utils.value_is_in_literal(task_type, TaskSubType):
        BrickService.log_brick_error(
            task_class,
            f"The task_type '{task_type}' for the task is invalid: {task_class.__name__}. Available values: {Utils.get_literal_values(TaskSubType)}")
        return

    # Check the input, output and config specs
    try:

        task_class.input_specs = IOSpecsHelper.check_input_specs(task_class.input_specs, task_class)
        task_class.output_specs = IOSpecsHelper.check_output_specs(task_class.output_specs, task_class)
        ParamSpecHelper.check_config_specs(task_class.config_specs)

    except Exception as err:
        BrickService.log_brick_error(
            task_class, f"Invalid specs for the task : {task_class.__name__}. {str(err)}")
        return

    # Set the default style if not defined
    if not style:
        style = get_task_default_style(task_class)
    elif not style.background_color or not style.icon_color:
        style.copy_from_style(get_task_default_style(task_class))

    related_resource_typing_name = related_resource._typing_name if related_resource else None

    register_gws_typing_class(object_class=task_class,
                              object_type="TASK",
                              unique_name=unique_name,
                              object_sub_type=task_type,
                              human_name=human_name,
                              short_description=short_description,
                              hide=hide,
                              style=style,
                              related_model_typing_name=related_resource_typing_name,
                              deprecated_since=deprecated_since,
                              deprecated_message=deprecated_message,
                              deprecated=deprecated)


def get_task_default_style(task_class: Type[Task]) -> TypingStyle:
    """Get the default style for a task, use the first input style or the first output style
    """
    default_typing_name = None
    first_input = task_class.input_specs.get_first_spec()
    if first_input:
        default_typing_name = first_input.get_default_resource_type()._typing_name
    else:
        first_output = task_class.output_specs.get_first_spec()
        if first_output:
            default_typing_name = first_output.get_default_resource_type()._typing_name

    if default_typing_name:
        typing = TypingManager.get_typing_from_name(default_typing_name)
        if typing and typing.style:
            return typing.style

    return TypingStyle.default_task()
