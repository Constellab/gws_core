

from gws_core.config.param.param_spec_helper import ParamSpecHelper
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_service import ScenarioService
from gws_core.scenario.task.scenario_param import ScenarioParam
from gws_core.scenario.task.scenario_resource import ScenarioResource
from gws_core.scenario.task.select_scenario import SelectScenario
from gws_core.task.task_runner import TaskRunner
from gws_core.test.base_test_case import BaseTestCase


# test_scenario_tasks
class TestScenarioTasks(BaseTestCase):

    def test_scenario_params(self):
        scenario = ScenarioService.create_scenario(title="test")

        param = ScenarioParam()
        config_params = ParamSpecHelper.build_config_params({"scenario": param}, {"scenario": scenario.id})

        data: Scenario = config_params["scenario"]
        self.assertIsInstance(data, Scenario)
        self.assertEqual(data.id, scenario.id)
        self.assertEqual(data.title, scenario.title)

    def test_select_scenario(self):
        scenario = ScenarioService.create_scenario(title="test 2")

        task_runner = TaskRunner(SelectScenario, params={"scenario": scenario.id})
        result = task_runner.run()

        scenario_resource: ScenarioResource = result['scenario']
        self.assertIsInstance(scenario_resource, ScenarioResource)
        self.assertEqual(scenario_resource.scenario_id, scenario.id)
        self.assertEqual(scenario_resource.get_scenario().title, 'test 2')
