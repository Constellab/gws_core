# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import Callable, Type

from ..model.typing_register_decorator import register_typing_class
from ..user.user_group import UserGroup
from .task import Task


def task_decorator(unique_name: str, allowed_user: UserGroup = UserGroup.USER,
                   human_name: str = "", short_description: str = "", hide: bool = False) -> Callable:
    """ Decorator to be placed on all the tasks. A task not decorated will not be runnable.
    It define static information about the task

    :param name_unique: a unique name for this task in the brick. Only 1 task in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the tasks
    :type name_unique: str
    :param allowed_user: role needed to run the task. By default all user can run it. It Admin, the user need to be an admin of the lab to run the task
    :type allowed_user: ProtocolAllowedUser, optional
    :param human_name: optional name that will be used in the interface when viewing the tasks. Must not be longer than 20 caracters
                        If not defined, the name_unique will be used
    :type human_name: str, optional
    :param short_description: optional description that will be used in the interface when viewing the tasks. Must not be longer than 100 caracters
    :type short_description: str, optional
    :param hide: Only the task with hide=False will be available in the interface(web platform), other will be hidden.
                It is useful for task that are not meant to be viewed in the interface (like abstract classes), defaults to False
    :type hide: bool, optional

    """
    def decorator(task_class: Type[Task]):
        if not issubclass(task_class, Task):
            raise Exception(
                f"The task_decorator is used on the class: {task_class.__name__} and this class is not a sub class of Task")

        register_typing_class(object_class=task_class, object_type="TASK", unique_name=unique_name,
                              human_name=human_name, short_description=short_description, hide=hide)

        # set the allowed user for the task
        task_class._allowed_user = allowed_user

        return task_class
    return decorator