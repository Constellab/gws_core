# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Callable, Type

from gws_core.resource.resource import Resource

from ..brick.brick_service import BrickService
from ..config.param.param_spec_helper import ParamSpecHelper
from ..core.utils.utils import Utils
from ..io.io_spec_helper import IOSpecsHelper
from ..model.typing_register_decorator import register_gws_typing_class
from ..user.user_group import UserGroup
from .task import Task
from .task_typing import TaskSubType


def task_decorator(unique_name: str, allowed_user: UserGroup = UserGroup.USER,
                   human_name: str = "", short_description: str = "", hide: bool = False,
                   deprecated_since: str = None, deprecated_message: str = None) -> Callable:
    """ Decorator to be placed on all the tasks. A task not decorated will not be runnable.
    It define static information about the task

    :param unique_name: a unique name for this task in the brick. Only 1 task in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the tasks
    :type unique_name: str
    :param allowed_user: role needed to run the task. By default all user can run it. It Admin, the user need to be an admin of the lab to run the task
    :type allowed_user: ProtocolAllowedUser, optional
    :param human_name: optional name that will be used in the interface when viewing the tasks. Must not be longer than 20 caracters
                        If not defined, the unique_name will be used
    :type human_name: str, optional
    :param short_description: optional description that will be used in the interface when viewing the tasks. Must not be longer than 100 caracters
    :type short_description: str, optional
    :param hide: Only the task with hide=False will be available in the interface(web platform), other will be hidden.
                It is useful for task that are not meant to be viewed in the interface (like abstract classes), defaults to False
    :type hide: bool, optional
    :param deprecated_since: To provide when the object is deprecated. It must be a version string like 1.0.0 to
                            tell at which version the object became deprecated, defaults to None
    :type deprecated_since: str, optional
    :param deprecated_message: Active when deprecated_since is provided. It describe a message about the deprecation.
                For example you can provide the name of another object to use instead, defaults to None
    :type deprecated_message: str, optional

    """
    def decorator(task_class: Type[Task]):
        decorate_task(task_class, unique_name=unique_name, task_type='TASK', allowed_user=allowed_user,
                      human_name=human_name, short_description=short_description, hide=hide,
                      deprecated_since=deprecated_since, deprecated_message=deprecated_message)

        return task_class
    return decorator


def decorate_task(
        task_class: Type[Task], unique_name: str,
        task_type: TaskSubType, related_resource: Type[Resource] = None,
        allowed_user: UserGroup = UserGroup.USER,
        human_name: str = "", short_description: str = "", hide: bool = False,
        deprecated_since: str = None, deprecated_message: str = None):
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

    related_resource_typing_name = related_resource._typing_name if related_resource else None

    register_gws_typing_class(object_class=task_class, object_type="TASK", unique_name=unique_name,
                              object_sub_type=task_type, human_name=human_name, short_description=short_description,
                              hide=hide, related_model_typing_name=related_resource_typing_name,
                              deprecated_since=deprecated_since, deprecated_message=deprecated_message)

    # set the allowed user for the task
    task_class._allowed_user = allowed_user
