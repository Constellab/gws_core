from typing import cast

from gws_core import (
    BaseTestCase,
    ProcessFactory,
    ProtocolModel,
    Scenario,
    ScenarioService,
    ScenarioStatus,
    TaskModel,
)
from gws_core.impl.robot.robot_resource import Robot, RobotFood
from gws_core.process.process_model import ProcessModel
from gws_core.process.process_types import ProcessStatus
from gws_core.resource.resource_model import ResourceModel
from gws_core.scenario.scenario_run_service import ScenarioRunService

from ..protocol_examples import (
    NestedProtocolTest,
    RobotWithSugarProtocolTest,
    SimpleProtocolTest,
    SubProtocolTest,
)


# test_protocol
class TestProtocol(BaseTestCase):
    def test_protocol(self):
        query = ProtocolModel.select()
        count = len(query)

        # create a chain
        scenario: Scenario = ScenarioService.create_scenario_from_protocol_type(SimpleProtocolTest)

        query = ProtocolModel.select()
        self.assertEqual(len(query), count + 1)

        scenario = ScenarioRunService.run_scenario(scenario=scenario)

        self.assertEqual(len(scenario.get_task_models()), 7)
        self.assertEqual(scenario.status, ScenarioStatus.SUCCESS)

    def test_advanced_protocol(self):
        query = ProtocolModel.select()
        count = len(query)

        scenario: Scenario = ScenarioService.create_scenario_from_protocol_type(NestedProtocolTest)
        super_proto: ProtocolModel = scenario.protocol_model

        self.assertEqual(ProtocolModel.select().count(), count + 2)

        mini_proto: ProtocolModel = cast(ProtocolModel, super_proto.get_process("mini_proto"))
        p1 = mini_proto.get_process("p1")
        self.assertTrue(mini_proto.is_interfaced_with(p1.instance_name))
        p2 = mini_proto.get_process("p2")
        self.assertTrue(mini_proto.is_outerfaced_with(p2.instance_name))

        scenario = ScenarioRunService.run_scenario(scenario=scenario)

        super_proto = cast(ProtocolModel, ProtocolModel.get_by_id(super_proto.id))

        query = ProtocolModel.select()
        self.assertEqual(len(query), count + 2)

    def test_optional_input(self):
        """Test the optional input if different scenarios
        1. It is connected and provided, so we wait for it
        2. It is not connected
        3. It is connected but not provided (None)
        """
        scenario: Scenario = ScenarioService.create_scenario_from_protocol_type(
            RobotWithSugarProtocolTest
        )

        scenario = ScenarioRunService.run_scenario(scenario=scenario)

        eat_1: TaskModel = cast(TaskModel, scenario.protocol_model.get_process("eat_1"))
        food: RobotFood = cast(RobotFood, eat_1.inputs.get_resource_model("food"))

        self.assertIsNotNone(food)

        # check that the RobotEat used the sugar food.
        # if yes, this will mean that the process eat waited for the food process to end
        # even if the food input of eat is optional
        robot_input: Robot = cast(
            Robot, cast(ResourceModel, eat_1.inputs.get_resource_model("robot")).get_resource()
        )
        robot_output: Robot = cast(
            Robot, cast(ResourceModel, eat_1.outputs.get_resource_model("robot")).get_resource()
        )
        # 2 = food weight, 10 sugar multiplicator
        self.assertEqual(robot_output.weight, robot_input.weight + (2 * 10))

        # Check that the eat_2 was called even if the food input (optional) is not plug
        eat_2: TaskModel = cast(TaskModel, scenario.protocol_model.get_process("eat_2"))
        robot_output_2: Robot = cast(
            Robot, cast(ResourceModel, eat_2.outputs.get_resource_model("robot")).get_resource()
        )
        # If this doesn't work, this mean that the process eat_2 was not called because it misses an optional input
        self.assertEqual(robot_output_2.weight, robot_output.weight + 5)  # 5 = food weight

    def test_processes(self):
        protocol: ProtocolModel = ProcessFactory.create_protocol_model_from_type(
            NestedProtocolTest
        )

        mini_proto: ProtocolModel = cast(ProtocolModel, protocol.get_process("mini_proto"))
        self.assertIsInstance(mini_proto, ProtocolModel)

        p2 = mini_proto.get_process("p2")
        self.assertIsInstance(p2, TaskModel)

        # test get next process
        next_processes = mini_proto.get_direct_next_processes("p2")
        self._check_process_set(next_processes, SubProtocolTest.p2_direct_next)

        # test get all next processes
        next_processes = mini_proto.get_all_next_processes("p2")
        self._check_process_set(next_processes, NestedProtocolTest.p2_next)

        # test get previous processes
        previous_processes = mini_proto.get_direct_previous_processes("p2")
        self._check_process_set(previous_processes, SubProtocolTest.p2_direct_previous)

        # test get error process
        p2.status = ProcessStatus.ERROR
        error_processes = protocol.get_error_tasks()
        self.assertEqual(len(error_processes), 1)
        self.assertEqual(error_processes[0], p2)

    def _check_process_set(
        self, processes: set[ProcessModel], expected_processes: set[str]
    ) -> None:
        self.assertEqual(len(processes), len(expected_processes))
        for process in processes:
            self.assertTrue(process.instance_name in expected_processes)
