from abc import abstractmethod
from collections.abc import Callable
from typing import final

from gws_core.brick.brick_service import BrickService
from gws_core.config.config_params import ConfigParams
from gws_core.core.utils.utils import Utils
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.model.typing_deprecated import TypingDeprecated
from gws_core.model.typing_style import TypingStyle
from gws_core.task.converter.converter import Converter, decorate_converter

from ...resource.resource import Resource
from ..task_decorator import task_decorator


def transformer_decorator(
    unique_name: str,
    resource_type: type[Resource],
    human_name: str = "",
    short_description: str = "",
    hide: bool = False,
    style: TypingStyle | None = None,
    deprecated: TypingDeprecated | None = None,
) -> Callable:
    """
    Decorator to place on a task instead of task_decorator. This create a specific task to transform the resource.

    :param unique_name: a unique name for this task in the brick. Only 1 task in the current brick can have this name.
                        //!\\ DO NOT MODIFIED THIS NAME ONCE IS DEFINED //!\\
                        It is used to instantiate the tasks
    :type unique_name: str
    :param resource_type: type of the resource transformed by this transformer
    :type resource_type: Type[Resource]
    :param human_name: optional name that will be used in the interface when viewing the tasks.
                        If not defined, the unique_name will be used
    :type human_name: str, optional
    :param short_description: optional description that will be used in the interface when viewing the tasks. Must not be longer than 255 caracters.
    :type short_description: str, optional
    :param hide: Only the task with hide=False will be available in the interface(web platform), other will be hidden.
                It is useful for task that are not meant to be viewed in the interface (like abstract classes), defaults to False
    :type hide: bool, optional
    :param style: style of the task, view TypingStyle object for more info. If not provided, takes the style of resource_type, defaults to None
    :type style: TypingStyle, optional
    :param deprecated: object to tell that the object is deprecated. See TypingDeprecated for more info, defaults to None
    :type deprecated: TypingDeprecated, optional
    """

    def decorator(task_class: type[Transformer]):
        if not Utils.issubclass(task_class, Transformer):
            BrickService.log_brick_error(
                task_class,
                f"The transformer_decorator is used on the class: {task_class.__name__} and this class is not a sub class of Transformer",
            )
            return task_class

        # Force the input and output specs
        task_class.input_specs = InputSpecs({"resource": resource_type})
        task_class.output_specs = OutputSpecs({"resource": resource_type})

        decorate_converter(
            task_class=task_class,
            unique_name=unique_name,
            task_type="TRANSFORMER",
            source_type=resource_type,
            target_type=resource_type,
            related_resource=resource_type,
            human_name=human_name,
            short_description=short_description,
            hide=hide,
            style=style,
            deprecated=deprecated,
        )

        return task_class

    return decorator


@task_decorator("Transformer", hide=True)
class Transformer(Converter):
    @final
    def convert(
        self, source: Resource, params: ConfigParams, target_type: type[Resource]
    ) -> Resource:
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
