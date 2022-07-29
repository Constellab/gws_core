# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import final

from gws_core.config.config_types import ConfigParams, ConfigSpecs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.resource.resource import Resource
from gws_core.task.action.actions import ActionsManager
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs

# def action_task_decorator(task_class: Type['ActionsTask'], unique_name: str,
#                           source_type: Type[Resource] = Resource, target_type: Type[Resource] = Resource,
#                           allowed_user: UserGroup = UserGroup.USER,
#                           human_name: str = "", short_description: str = "", hide: bool = False,
#                           deprecated_since: str = None, deprecated_message: str = None) -> None:
#     def decorator(task_class: Type[Task]):

#     if not Utils.issubclass(task_class, ActionsTask):
#         BrickService.log_brick_error(
#             task_class,
#             f"The action_task_decorator is used on the class: {task_class.__name__} and this class is not a sub class of ActionsTask")
#         return

#     # force the input and output specs
#     task_class.input_specs = {"actions": InputSpec(Actions, human_name="Actions",
#                                                    short_description="List of actions to modify the source resource"),
#                               "source": InputSpec(source_type, human_name="Source")}
#     task_class.output_specs = {"target": OutputSpec(target_type)}

#     # register the task and set the human_name and short_description dynamically based on resource
#     decorate_task(task_class, unique_name, human_name=human_name,
#                   task_type="ACTIONS_TASK", short_description=short_description, allowed_user=allowed_user, hide=hide,
#                   deprecated_since=deprecated_since, deprecated_message=deprecated_message)


@task_decorator("ActionsTask", hide=True)
class ActionsTask(Task):

    actions_input_name: str = 'actions'
    source_input_name: str = 'source'
    target_output_name: str = 'target'

    input_specs = {"actions": InputSpec(ActionsManager, human_name="Actions",
                                        short_description="List of actions to modify the source resource"),
                   "source": InputSpec(Resource, human_name="Source")}
    output_specs = {"target": OutputSpec(Resource)}

    # Override the config_spec to define custom spec for the importer
    config_specs: ConfigSpecs = {}

    @final
    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # retrieve the source
        source: Resource = inputs.get(self.source_input_name)

        # retrieve the action
        actions: ActionsManager = inputs.get(self.actions_input_name)

        target = source

        for action in actions.get_actions():
            # execute the action
            target = action.execute(target)

        if target is None:
            raise Exception('The target resource is None')

        if target.name is None:
            # set the target name source name
            target.name = source.name

        return {self.target_output_name: target}
