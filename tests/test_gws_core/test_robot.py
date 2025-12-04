from unittest import TestCase

from gws_core import TaskRunner
from gws_core.impl.robot.robot_resource import Robot  # local import of the resource
from gws_core.impl.robot.robot_tasks import RobotMove  # local import of the task


class TestRobotMove(TestCase):
    def test_robot_move(self):
        # create an empty robot
        robot_output = Robot.empty()

        # create a task runner and configure it, then run it
        runner = TaskRunner(
            task_type=RobotMove,
            params={"moving_step": 3, "direction": "south"},
            inputs={"robot": robot_output},
        )
        outputs = runner.run()

        # retrieve the robot output
        robot_output: Robot = outputs["robot"]

        # check the robot position, y should be -3 as he went south
        self.assertEqual(robot_output.position, [0, -3])
