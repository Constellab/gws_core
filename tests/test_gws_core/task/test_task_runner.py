from unittest import TestCase

from gws_core import (
    BadRequestException,
    ConfigParams,
    JSONDict,
    OutputSpecs,
    Resource,
    Table,
    Task,
    TaskInputs,
    TaskOutputs,
    TaskRunner,
    resource_decorator,
    task_decorator,
)
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotMove
from gws_core.io.io_exception import (
    InvalidInputsException,
    InvalidOutputsException,
    MissingInputResourcesException,
)
from gws_core.io.io_spec import InputSpec, OutputSpec


@task_decorator("TaskRunnerProgress")
class TaskRunnerProgress(Task):
    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        self.log_info_message("Hello")
        self.update_progress_value(50, "Hello 50%")


@task_decorator("TaskRunnerOutputError")
class TaskRunnerOutputError(Task):
    output_specs: OutputSpecs = OutputSpecs({"test": InputSpec(Table)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {"test": JSONDict()}


@task_decorator("TaskRunnerOutputMissing")
class TaskRunnerOutputMissing(Task):
    output_specs: OutputSpecs = OutputSpecs({"test": OutputSpec(Table)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {}


@resource_decorator("ResourceCheckError")
class ResourceCheckError(Resource):
    def check_resource(self) -> str:
        return "Invalid resource"


@task_decorator("TaskRunnerInvalidResource")
class TaskRunnerInvalidResource(Task):
    output_specs: OutputSpecs = OutputSpecs({"test": OutputSpec(ResourceCheckError)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {"test": ResourceCheckError()}


# test_task_runner
class TestTaskRunner(TestCase):
    def test_task_tester(self):
        """Method to test the Task tester class"""

        task_tester: TaskRunner = TaskRunner(
            RobotMove, {"moving_step": 10, "direction": "south"}, {"robot": Robot.empty()}
        )

        output: TaskOutputs = task_tester.run()

        robot: Robot = output["robot"]
        self.assertEqual(robot.position, [0, -10])

    def test_missing_input(self):
        task_tester: TaskRunner = TaskRunner(
            RobotMove, {"moving_step": 10, "direction": "south"}, {}
        )

        with self.assertRaises(MissingInputResourcesException):
            task_tester.run()

    def test_wrong_config(self):
        with self.assertRaises(BadRequestException):
            task_tester: TaskRunner = TaskRunner(
                RobotMove, {"moving_step": "test", "direction": "south"}, {"robot": Robot.empty()}
            )

            task_tester.run()

    def test_progress(self):
        task_tester: TaskRunner = TaskRunner(TaskRunnerProgress)

        task_tester.run()

    def test_wrong_output(self):
        task_tester: TaskRunner = TaskRunner(TaskRunnerOutputError)

        with self.assertRaises(InvalidOutputsException):
            task_tester.run()

    def test_missing_output(self):
        task_tester: TaskRunner = TaskRunner(TaskRunnerOutputMissing)

        with self.assertRaises(InvalidOutputsException):
            task_tester.run()

    def test_invalid_resource_ouptut(self):
        task_tester: TaskRunner = TaskRunner(TaskRunnerInvalidResource)

        with self.assertRaises(InvalidOutputsException):
            task_tester.run()

    def test_invalid_input(self):
        task_tester: TaskRunner = TaskRunner(RobotMove, {}, {"robot": JSONDict()})

        with self.assertRaises(InvalidInputsException):
            task_tester.run()
