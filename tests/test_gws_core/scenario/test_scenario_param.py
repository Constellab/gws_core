

from gws_core.config.param.param_spec_helper import ParamSpecHelper
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_service import ScenarioService
from gws_core.scenario.task.scenario_param import ScenarioParam
from gws_core.test.base_test_case import BaseTestCase


# test_scenario_param
class TestScenarioParam(BaseTestCase):

    def test_scenario_params(self):
        scenario = ScenarioService.create_scenario(title="test")

        param = ScenarioParam()
        config_params = ParamSpecHelper.build_config_params({"scenario": param}, {"scenario": scenario.id})

        data: Scenario = config_params["scenario"]
        self.assertIsInstance(data, Scenario)
        self.assertEqual(data.id, scenario.id)
        self.assertEqual(data.title, scenario.title)
