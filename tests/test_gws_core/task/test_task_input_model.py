
from typing import List

from gws_core.impl.robot.robot_protocol import (CreateSimpleRobot,
                                                MoveSimpleRobot)
from gws_core.impl.robot.robot_tasks import RobotCreate, RobotMove
from gws_core.process.process_model import ProcessModel
from gws_core.protocol.protocol import Protocol
from gws_core.protocol.protocol_decorator import protocol_decorator
from gws_core.protocol.protocol_model import ProtocolModel
from gws_core.protocol.protocol_spec import ProcessSpec
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.task.plug import Sink
from gws_core.task.task_input_model import TaskInputModel
from gws_core.task.task_model import TaskModel
from gws_core.test.base_test_case import BaseTestCase


@protocol_decorator("RobotSuperTravelProto")
class RobotSuperTravelProto(Protocol):
    def configure_protocol(self) -> None:

        move: ProcessSpec = self.add_process(RobotMove, "move")

        self.add_interface('robot', move, 'robot')
        self.add_outerface('robot', move, 'robot')


@protocol_decorator("RobotMainTravel", )
class RobotMainTravel(Protocol):

    def configure_protocol(self) -> None:

        facto: ProcessSpec = self.add_process(RobotCreate, "facto")
        sub_travel: ProcessSpec = self.add_process(RobotSuperTravelProto, "sub_travel")

        # define the protocol output
        sink: ProcessSpec = self.add_process(Sink, 'sink')

        self.add_connectors([
            (facto >> 'robot', sub_travel << 'robot'),
            (sub_travel >> 'robot', sink << 'resource'),
        ])


# test_task_input_model
class TestTaskInputModel(BaseTestCase):

    def test_task_input_model(self):
        scenario: ScenarioProxy = ScenarioProxy(RobotMainTravel)
        scenario.run()

        ################################ CHECK TASK INPUT ################################
        # Check if the Input resource was set
        sink: ProcessModel = scenario._scenario.protocol_model.get_process('sink')
        task_inputs: List[TaskInputModel] = list(
            TaskInputModel.get_by_resource_model(sink.inputs.get_resource_model('resource').id))
        self.assertEqual(len(task_inputs), 1)
        self.assertEqual(task_inputs[0].is_interface, False)
        self.assertEqual(task_inputs[0].port_name, "resource")

        # Check the TaskInput with a sub process and a resource that is an interface
        sub_travel: ProtocolModel = scenario._scenario.protocol_model.get_process('sub_travel')
        sub_move: TaskModel = sub_travel.get_process('move')
        task_inputs = list(TaskInputModel.get_by_task_model(sub_move.id))
        self.assertEqual(len(task_inputs), 1)
        self.assertEqual(task_inputs[0].is_interface, True)

    def test_task_input_model_select(self):
        # Test the select of input model task and delete by scenario
        scenario_1: ScenarioProxy = ScenarioProxy(CreateSimpleRobot)
        scenario_1.run()

        scenario_2: ScenarioProxy = ScenarioProxy(CreateSimpleRobot)
        scenario_2.run()

        task_input: TaskInputModel = TaskInputModel.get_by_scenario(scenario_1._scenario.id).first()
        self.assertIsNotNone(task_input)
        self.assertEqual(TaskInputModel.get_by_scenario(scenario_1._scenario.id).count(), 1)
        self.assertEqual(TaskInputModel.get_by_resource_model(task_input.resource_model.id).count(), 1)
        self.assertEqual(TaskInputModel.get_by_task_model(task_input.task_model.id).count(), 1)

        # Create another scenario that use the previous resource
        scenario_3: ScenarioProxy = ScenarioProxy(MoveSimpleRobot)
        scenario_3.get_protocol().get_process('source').set_param('resource_id', task_input.resource_model.id)
        scenario_3.run()
        # Get all the task input where the resource is used in another scenario
        task_input = TaskInputModel.get_other_scenarios(
            [task_input.resource_model.id], scenario_1._scenario.id).first()
        self.assertEqual(task_input.scenario.id, scenario_3._scenario.id)
