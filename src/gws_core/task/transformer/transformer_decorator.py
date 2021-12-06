# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from typing import Type

from ...resource.resource import Resource
from ...user.user_group import UserGroup
from ..task import Task
from ..task_decorator import decorate_task


def transformer_decorator(unique_name: str, resource_type: Type[Resource],
                          allowed_user: UserGroup = UserGroup.USER,
                          human_name: str = "", short_description: str = "", hide: bool = False):
    """ Decorator to place on a task instead of task_decorator. This create a specific task to transform the resource.
    :param unique_name: a unique name for this task in the brick. Only 1 task in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the tasks
    :type unique_name: str
    :param resource_type: type of the resource transformed by this transformer
    :type resource_type: Type[Resource]
    :param allowed_user: role needed to run the task. By default all user can run it. It Admin, the user need to be an admin of the lab to run the task
    :type allowed_user: ProtocolAllowedUser, optional
    :return: [description]
    :rtype: Callable
    """

    def decorator(task_class: Type[Task]):

        # Force the input and output specs
        task_class.input_specs = {'resource': resource_type}
        task_class.output_specs = {'resource': resource_type}

        decorate_task(task_class=task_class, unique_name=unique_name, task_type='TRANSFORMER',
                      related_resource=resource_type, allowed_user=allowed_user, human_name=human_name,
                      short_description=short_description, hide=hide)

        return task_class
    return decorator
