

from gws_core import (CheckBeforeTaskResult, ResourceModel, Robot, Source,
                      Switch2, TaskOutputs, TaskRunner)
from gws_core.test.base_test_case import BaseTestCase


class TestPlug(BaseTestCase):

    async def test_source(self):
        """Test the source task
        """
        robot: Robot = Robot.empty()
        robot_model: ResourceModel = ResourceModel.from_resource(robot)
        robot_model.save()

        task_tester = TaskRunner(Source, {'resource_uri': robot_model.uri})

        outputs: TaskOutputs = await task_tester.run()

        robot_o: Robot = outputs['resource']
        self.assertEqual(robot_o._model_uri, robot_model.uri)

    async def test_switch(self):
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

        outputs: TaskOutputs = await task_tester.run()

        robot_o: Robot = outputs['resource']
        self.assertEqual(robot_o, robot_2)

    async def test_fifo(self):
        """Test the switch2 task
        """
        robot: Robot = Robot.empty()

        task_tester = TaskRunner(Switch2)
        task_tester.set_input('resource_1', robot)

        # check that the task is not ready
        result: CheckBeforeTaskResult = task_tester.check_before_run()
        self.assertTrue(result['result'])

        outputs: TaskOutputs = await task_tester.run()

        robot_o: Robot = outputs['resource']
        self.assertEqual(robot_o, robot)
