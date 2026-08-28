from typing import cast

from gws_core import (
    BaseTestCase,
    ConfigParams,
    ProcessFactory,
    ProtocolModel,
    ProtocolService,
    ResourceModel,
    Scenario,
    ScenarioService,
    Task,
    TaskInputs,
    TaskModel,
    TaskOutputs,
    task_decorator,
)
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotCreate
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.scenario.scenario_exception import ScenarioRunException
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.scenario_run_service import ScenarioRunService
from gws_core.task.plug.input_task import InputTask
from gws_core.test.test_helper import TestHelper

from ..protocol_examples import SimpleProtocolTest


@task_decorator(unique_name="RunAfterTask")
class RunAfterTask(Task):
    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {}

    def run_after_task(self) -> None:
        raise Exception("run_after_task")


# test_task
class TestTask(BaseTestCase):
    def test_task_singleton(self):
        p0: TaskModel = ProcessFactory.create_task_model_from_type(task_type=RobotCreate)
        p1: TaskModel = ProcessFactory.create_task_model_from_type(task_type=RobotCreate)

        self.assertTrue(p0.id != p1.id)

    def test_process(self):
        scenario: Scenario = ScenarioService.create_scenario_from_protocol_type(SimpleProtocolTest)
        proto: ProtocolModel = scenario.protocol_model

        p0: TaskModel = cast(TaskModel, proto.get_process("p0"))

        self.assertTrue(p0.created_by.is_sysuser)
        self.assertEqual(proto.created_by, TestHelper.get_system_user())

        # configure p2 through the service so the value is persisted before the run
        ProtocolService.configure_process(proto.id, "p2", {"food_weight": "5.6"})

        self.assertEqual(scenario.created_by, TestHelper.get_system_user())

        scenario = ScenarioRunService.run_scenario(scenario=scenario)

        # Refresh the processes
        protocol: ProtocolModel = scenario.protocol_model
        self.assertEqual(protocol.created_by, TestHelper.get_system_user())

        p0 = cast(TaskModel, protocol.get_process("p0"))
        self.assertEqual(protocol.created_by, TestHelper.get_system_user())

        p1 = cast(TaskModel, protocol.get_process("p1"))
        p2 = cast(TaskModel, protocol.get_process("p2"))
        p3 = cast(TaskModel, protocol.get_process("p3"))
        elon: Robot = cast(
            Robot, cast(ResourceModel, p0.outputs.get_resource_model("robot")).get_resource()
        )

        self.assertEqual(elon.weight, 70)

        # check p1
        p1_out: Robot = cast(
            Robot, cast(ResourceModel, p1.outputs.get_resource_model("robot")).get_resource()
        )
        self.assertEqual(
            p1_out.position[1],
            elon.position[1] + p1.config.get_value("moving_step"),
        )
        self.assertEqual(p1_out.weight, elon.weight)

        # check p2
        p2_out: Robot = cast(
            Robot, cast(ResourceModel, p2.outputs.get_resource_model("robot")).get_resource()
        )
        p2_in: Robot = cast(
            Robot, cast(ResourceModel, p2.inputs.get_resource_model("robot")).get_resource()
        )
        self.assertEqual(
            p2_out.position,
            p2_in.position,
        )
        self.assertEqual(
            p2_out.weight,
            p2_in.weight + p2.config.get_value("food_weight"),
        )

        # check p3
        p3_out: Robot = cast(
            Robot, cast(ResourceModel, p3.outputs.get_resource_model("robot")).get_resource()
        )
        p3_in: Robot = cast(
            Robot, cast(ResourceModel, p3.inputs.get_resource_model("robot")).get_resource()
        )
        self.assertEqual(
            p3_out.position[1],
            p3_in.position[1] + p3.config.get_value("moving_step"),
        )
        self.assertEqual(
            p3_out.weight,
            p3_in.weight,
        )

        res = ResourceModel.get_by_id(
            cast(ResourceModel, p3.outputs.get_resource_model("robot")).id
        )
        self.assertTrue(isinstance(res, ResourceModel))

        self.assertTrue(len(cast(dict, p0.progress_bar.data)["messages"]) >= 2)  # noqa: PLR2004

        scenario.to_dto()

    def test_after_run(self):
        """Test that the after run method is called
        To test it, we check that it raised an exception
        """

        scenario: ScenarioProxy = ScenarioProxy()
        scenario.get_protocol().add_process(RunAfterTask, "run")

        with self.assertRaises(ScenarioRunException):
            scenario.run()

    def test_input_task(self):
        """
        Test that the use of a resource in a source config is saved in the database so we can retrieve which
        Input task uses a resource. Even if the scenario that uses the resource was not runned.
        """
        robot_model = ResourceModel.save_from_resource(
            Robot.empty(), origin=ResourceOrigin.UPLOADED
        )

        scenario: ScenarioProxy = ScenarioProxy()
        task = scenario.get_protocol().add_task(
            InputTask, "source", {InputTask.config_name: robot_model.id}
        )

        tasks = list(TaskModel.select().where(TaskModel.source_config_id == robot_model.id))
        # Check that the use of the robot in the scenario was saved

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].id, task.get_model().id)
