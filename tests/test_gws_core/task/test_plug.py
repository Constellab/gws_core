

from gws_core import (CheckBeforeTaskResult, ResourceModel, Source, Switch2,
                      TaskOutputs, TaskRunner)
from gws_core.experiment.experiment_interface import IExperiment
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotCreate
from gws_core.process.process_interface import IProcess
from gws_core.protocol.protocol_interface import IProtocol
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.task.plug import Sink
from gws_core.test.base_test_case import BaseTestCase


# test_plug
class TestPlug(BaseTestCase):

    def test_source(self):
        """Test the source task
        """
        robot: Robot = Robot.empty()
        robot_model: ResourceModel = ResourceModel.save_from_resource(robot, origin=ResourceOrigin.UPLOADED)

        task_tester = TaskRunner(Source, {'resource_id': robot_model.id})

        outputs: TaskOutputs = task_tester.run()

        robot_o: Robot = outputs['resource']
        self.assertEqual(robot_o._model_id, robot_model.id)

    def test_sink(self):
        i_experiment: IExperiment = IExperiment()
        i_protocol: IProtocol = i_experiment.get_protocol()

        create: IProcess = i_protocol.add_task(RobotCreate, 'create')
        sink: IProcess = i_protocol.add_task(Sink, 'sink')
        i_protocol.add_connector(create >> 'robot', sink << 'resource')

        i_experiment.run()

        # check that the resource used in the sink was marked as output
        resource = create.refresh().get_output('robot')
        resource_model: ResourceModel = ResourceModel.get_by_id_and_check(resource._model_id)
        self.assertEqual(resource_model.flagged, True)

    def test_switch(self):
        """Test the switch2 task
        """
        robot: Robot = Robot.empty()
        robot_2: Robot = Robot.empty()

        task_tester = TaskRunner(Switch2, {'index': 2})
        task_tester.set_input('resource_1', robot)

        # check that the task is not ready
        result: CheckBeforeTaskResult = task_tester.check_before_run()
        self.assertFalse(result['result'])

        # check that the task is ready
        task_tester.set_input('resource_2', robot_2)
        result: CheckBeforeTaskResult = task_tester.check_before_run()
        self.assertTrue(result['result'])

        outputs: TaskOutputs = task_tester.run()

        robot_o: Robot = outputs['resource']
        self.assertEqual(robot_o, robot_2)

    def test_fifo(self):
        """Test the switch2 task
        """
        robot: Robot = Robot.empty()

        task_tester = TaskRunner(Switch2)
        task_tester.set_input('resource_1', robot)

        # check that the task is not ready
        result: CheckBeforeTaskResult = task_tester.check_before_run()
        self.assertTrue(result['result'])

        outputs: TaskOutputs = task_tester.run()

        robot_o: Robot = outputs['resource']
        self.assertEqual(robot_o, robot)
