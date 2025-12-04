from gws_core import CheckBeforeTaskResult, InputTask, ResourceModel, TaskOutputs, TaskRunner
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotCreate
from gws_core.process.process_proxy import ProcessProxy
from gws_core.protocol.protocol_proxy import ProtocolProxy
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.task.plug.output_task import OutputTask
from gws_core.task.plug.switch import Switch2
from gws_core.test.base_test_case import BaseTestCase


# test_plug
class TestPlug(BaseTestCase):
    def test_source(self):
        """Test the source task"""
        robot: Robot = Robot.empty()
        robot_model: ResourceModel = ResourceModel.save_from_resource(
            robot, origin=ResourceOrigin.UPLOADED
        )

        task_tester = TaskRunner(InputTask, {"resource_id": robot_model.id})

        outputs: TaskOutputs = task_tester.run()

        robot_o: Robot = outputs["resource"]
        self.assertEqual(robot_o.get_model_id(), robot_model.id)

    def test_output(self):
        i_scenario: ScenarioProxy = ScenarioProxy()
        i_protocol: ProtocolProxy = i_scenario.get_protocol()

        create: ProcessProxy = i_protocol.add_task(RobotCreate, "create")
        output: ProcessProxy = i_protocol.add_task(OutputTask, "output")
        i_protocol.add_connector(create >> "robot", output << "resource")

        i_scenario.run()

        # check that the resource used in the output was marked as output
        resource = create.refresh().get_output("robot")
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource.get_model_id())
        self.assertEqual(resource_model.flagged, True)

    def test_switch(self):
        """Test the switch2 task"""
        robot: Robot = Robot.empty()
        robot_2: Robot = Robot.empty()

        task_tester = TaskRunner(Switch2, {"index": 2})
        task_tester.set_input("resource_1", robot)

        # check that the task is not ready
        result: CheckBeforeTaskResult = task_tester.check_before_run()
        self.assertFalse(result["result"])

        # check that the task is ready
        task_tester.set_input("resource_2", robot_2)
        result: CheckBeforeTaskResult = task_tester.check_before_run()
        self.assertTrue(result["result"])

        outputs: TaskOutputs = task_tester.run()

        robot_o: Robot = outputs["resource"]
        self.assertEqual(robot_o, robot_2)
