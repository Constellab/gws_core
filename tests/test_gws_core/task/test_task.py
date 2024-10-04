

from abc import abstractmethod

from gws_core import (BaseTestCase, ConfigParams, ProcessFactory,
                      ProtocolModel, ProtocolService, ResourceModel, Scenario,
                      ScenarioService, Task, TaskInputs, TaskModel,
                      TaskOutputs, task_decorator)
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotCreate
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.scenario_run_service import ScenarioRunService
from gws_core.task.plug import Source
from gws_core.test.gtest import GTest

from ..protocol_examples import TestSimpleProtocol


@task_decorator(unique_name="RunAfterTask")
class RunAfterTask(Task):
    @abstractmethod
    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return None

    def run_after_task(self) -> None:
        raise Exception('run_after_task')


# test_task
class TestTask(BaseTestCase):

    def test_task_singleton(self):

        p0: TaskModel = ProcessFactory.create_task_model_from_type(
            task_type=RobotCreate)
        p1: TaskModel = ProcessFactory.create_task_model_from_type(
            task_type=RobotCreate)
        # p0.title = "First 'Create' task"
        # p0.description = "This is the description of the task"
        p0.save_full()

        self.assertTrue(p0.id != p1.id)

    def test_process(self):

        proto: ProtocolModel = ProtocolService.create_protocol_model_from_type(
            TestSimpleProtocol)

        p0: TaskModel = proto.get_process('p0')
        p1: TaskModel = proto.get_process('p1')
        p2: TaskModel = proto.get_process('p2')

        self.assertTrue(p0.created_by.is_sysuser)
        self.assertEqual(proto.created_by, GTest.user)

        p2.config.set_value('food_weight', '5.6')

        scenario: Scenario = ScenarioService.create_scenario_from_protocol_model(
            protocol_model=proto)

        self.assertEqual(scenario.created_by, GTest.user)

        scenario = ScenarioRunService.run_scenario(scenario=scenario)

        # Refresh the processes
        protocol: ProtocolModel = scenario.protocol_model
        self.assertEqual(protocol.created_by, GTest.user)

        p0 = protocol.get_process("p0")
        self.assertEqual(protocol.created_by, GTest.user)

        p1 = protocol.get_process("p1")
        p2 = protocol.get_process("p2")
        p3 = protocol.get_process("p3")
        elon: Robot = p0.outputs.get_resource_model('robot').get_resource()

        self.assertEqual(elon.weight, 70)

        # check p1
        self.assertEqual(
            p1.outputs.get_resource_model('robot').get_resource().position[1],
            elon.position[1] + p1.config.get_value('moving_step'))
        self.assertEqual(p1.outputs.get_resource_model(
            'robot').get_resource().weight, elon.weight)

        # check p2
        self.assertEqual(p2.outputs.get_resource_model('robot').get_resource().position,
                         p2.inputs.get_resource_model('robot').get_resource().position)
        self.assertEqual(p2.outputs.get_resource_model('robot').get_resource().weight, p2.inputs.get_resource_model(
            'robot').get_resource().weight + p2.config.get_value('food_weight'))

        # check p3
        self.assertEqual(p3.outputs.get_resource_model('robot').get_resource().position[1], p3.inputs.get_resource_model(
            'robot').get_resource().position[1] + p3.config.get_value('moving_step'))
        self.assertEqual(p3.outputs.get_resource_model('robot').get_resource().weight,
                         p3.inputs.get_resource_model('robot').get_resource().weight)

        res = ResourceModel.get_by_id(
            p3.outputs.get_resource_model('robot').id)
        self.assertTrue(isinstance(res, ResourceModel))

        self.assertTrue(
            len(p0.progress_bar.data["messages"]) >= 2)

        scenario.to_dto()

    def test_after_run(self):
        """Test that the after run method is called
        To test it, we check that it raised an exception
        """

        scenario: ScenarioProxy = ScenarioProxy()
        scenario.get_protocol().add_process(RunAfterTask, 'run')

        with self.assertRaises(Exception):
            scenario.run()

    def test_source_task(self):
        """
        Test that the use of a resource in a Source config is saved in the database so we can retrieve which
        Source task uses a resource. Even if the scenario that uses the resource was not runned.
        """
        robot_model = ResourceModel.save_from_resource(
            Robot.empty(), origin=ResourceOrigin.UPLOADED)

        scenario: ScenarioProxy = ScenarioProxy()
        task = scenario.get_protocol().add_task(
            Source, 'source', {Source.config_name: robot_model.id})

        tasks = (list(TaskModel.select().where(TaskModel.source_config_id == robot_model.id)))
        # Check that the use of the robot in the scenario was saved

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].id, task.get_model().id)
