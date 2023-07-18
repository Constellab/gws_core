# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from typing import final

from gws_core.config.config_params import ConfigParams
from gws_core.config.config_types import ConfigSpecs
from gws_core.io.io_spec import InputSpec, OutputSpec
from gws_core.io.io_specs import InputSpecs, OutputSpecs
from gws_core.resource.resource import Resource
from gws_core.task.action.actions_manager import ActionsManager
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator("ActionsTask", hide=True)
class ActionsTask(Task):

    actions_input_name: str = 'actions_manager'
    source_input_name: str = 'source'
    target_output_name: str = 'target'

    input_specs = InputSpecs({"actions_manager": InputSpec(ActionsManager, human_name="Actions",
                                                           short_description="List of actions to modify the source resource"),
                              "source": InputSpec(Resource, human_name="Source")})
    output_specs = OutputSpecs({"target": OutputSpec(Resource)})

    # Override the config_spec to define custom spec for the importer
    config_specs: ConfigSpecs = {}

    @final
    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        # retrieve the source
        source: Resource = inputs.get(self.source_input_name)

        # retrieve the action
        actions: ActionsManager = inputs.get(self.actions_input_name)

        target: Resource = source

        for action in actions.get_actions():
            # execute the action
            target = action.execute(target)

        if target is None:
            raise Exception('The target resource is None')

        if target.name is None:
            # set the target name source name
            target.name = source.name

        return {self.target_output_name: target}
