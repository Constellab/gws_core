from gws_core.process_run_stat.process_run_stat_model import ProcessRunStatModel
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_run_service import ScenarioRunService
from gws_core.scenario.scenario_service import ScenarioService
from gws_core.test.base_test_case import BaseTestCase

from test_gws_core.protocol_examples import SimpleProtocolTest


class TestProcessRunStat(BaseTestCase):
    def test_process_run_stat(self):
        scenario: Scenario = ScenarioService.create_scenario_from_protocol_type(SimpleProtocolTest)

        scenario = ScenarioRunService.run_scenario(scenario=scenario)

        stats = ProcessRunStatModel.select()
        self.assertEqual(len(stats), 8)
