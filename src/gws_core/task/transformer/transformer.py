# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from abc import abstractmethod
from typing import Type, final

from gws_core.brick.brick_service import BrickService
from gws_core.config.config_types import ConfigParams
from gws_core.core.utils.utils import Utils
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.task.converter.converter import Converter, decorate_converter

from ...resource.resource import Resource
from ...user.user_group import UserGroup
from ..task import Task
from ..task_decorator import task_decorator


def transformer_decorator(unique_name: str, resource_type: Type[Resource],
                          allowed_user: UserGroup = UserGroup.USER,
                          human_name: str = "", short_description: str = "", hide: bool = False,
                          deprecated_since: str = None, deprecated_message: str = None):
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

        if not Utils.issubclass(task_class, Transformer):
            BrickService.log_brick_error(
                task_class,
                f"The transformer_decorator is used on the class: {task_class.__name__} and this class is not a sub class of Transformer")
            return task_class

        # Force the input and output specs
        task_class.input_specs = InputSpecs({'resource': resource_type})
        task_class.output_specs = OutputSpecs({'resource': resource_type})

        decorate_converter(task_class=task_class, unique_name=unique_name, task_type='TRANSFORMER',
                           source_type=resource_type, target_type=resource_type, related_resource=resource_type,
                           allowed_user=allowed_user, human_name=human_name,
                           short_description=short_description, hide=hide,
                           deprecated_since=deprecated_since, deprecated_message=deprecated_message)

        return task_class
    return decorator


@task_decorator("Transformer", hide=True)
class Transformer(Converter):

    @final
    def convert(self, source: Resource, params: ConfigParams, target_type: Type[Resource]) -> Resource:
        target: Resource = self.transform(source, params)

        # copy the source name if the target name is not set
        if target.name is None:
            # set the target name source name
            target.name = source.name

        return target

    @abstractmethod
    def transform(self, source: Resource, params: ConfigParams) -> Resource:
        """Override this method to write the Transformer code

        :param source: resource to modifify, the source object can be directly modify as this is already a new copy
        :type source: Resource
        :param params: params for the transform
        :type params: ConfigParams
        :return: [description]
        :rtype: Resource
        """
