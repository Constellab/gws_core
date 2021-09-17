

from gws_core import TaskTester
from gws_core.config.config_types import ConfigParams
from gws_core.core.exception.exceptions.bad_request_exception import \
    BadRequestException
from gws_core.core.test.base_test_case import BaseTestCase
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotMove
from gws_core.io.io_exception import MissingInputResourcesException
from gws_core.process import process_model
from gws_core.task.task import Task
from gws_core.task.task_decorator import task_decorator
from gws_core.task.task_io import TaskInputs, TaskOutputs


@task_decorator("TaskTesterProgress")
class TaskTesterProgress(Task):
    async def run(self, config: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        self.add_progress_message('Hello')
        self.update_progress_value(50, 'Hello 50%')


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

    async def test_progress(self):
        task_tester: TaskTester = TaskTester(TaskTesterProgress)

        await task_tester.run()
