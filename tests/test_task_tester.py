

from gws_core import TaskTester
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.test.base_test_case import BaseTestCase
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotMove
from gws_core.io.io_exception import MissingInputResourcesException
from gws_core.task.task_io import TaskOutputs


class TestTaskTester(BaseTestCase):

    async def test_task_tester(self):
        """Method to test the Task tester class
        """

        task_tester: TaskTester = TaskTester(RobotMove,
                                             {'moving_step': 10, 'direction': 'south'},
                                             {'robot': Robot.empty()})

        output: TaskOutputs = await task_tester.run()

        robot: Robot = output['robot']
        self.assertEqual(robot.position, [0, -10])

    async def test_missing_input(self):
        task_tester: TaskTester = TaskTester(RobotMove,
                                             {'moving_step': 10, 'direction': 'south'},
                                             {})

        with self.assertRaises(MissingInputResourcesException):
            await task_tester.run()

    async def test_wrong_config(self):
        task_tester: TaskTester = TaskTester(RobotMove,
                                             {'moving_step': 'test', 'direction': 'south'},
                                             {'robot': Robot.empty()})

        with self.assertRaises(BadRequestException):
            await task_tester.run()
