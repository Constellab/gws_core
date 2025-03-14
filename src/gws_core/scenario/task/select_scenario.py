from gws_core.config.config_params import ConfigParams
from gws_core.io.io_spec import OutputSpec
from gws_core.io.io_specs import OutputSpecs
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.task.scenario_param import ScenarioParam
from gws_core.scenario.task.scenario_resource import ScenarioResource
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator("SelectScenario", human_name="Select a scenario",
                short_description="Select a scenario and return a ScenarioResource")
class SelectScenario(Task):
    """
    Task to select a scenario and return a ScenarioResource.

    This is useful when you want to manipulate a scenario from a task (like send a scenario to a lab).
    """

    output_specs = OutputSpecs({
        'scenario': OutputSpec(ScenarioResource, human_name="Selected scenario")
    })

    config_specs = {
        'scenario': ScenarioParam(human_name="Select a scenario"),
    }

    OUTPUT_NAME = 'scenario'
    CONFIG_NAME = 'scenario'

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        """ Run the task """

        scenario: Scenario = params.get_value('scenario')

        return {'scenario': ScenarioResource(scenario.id)}
