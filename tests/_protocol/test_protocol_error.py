# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import (BaseTestCase, CheckBeforeTaskResult, ConfigParams,
                      Experiment, ExperimentService, GTest, InputSpec,
                      OutputSpec, ProcessFactory, ProcessModel, ProcessSpec,
                      Protocol, ProtocolModel, ProtocolService, Resource,
                      RobotMove, Task, TaskInputs, TaskOutputs,
                      protocol_decorator, resource_decorator, task_decorator)
from gws_core.experiment.experiment_exception import ExperimentRunException
from gws_core.experiment.experiment_run_service import ExperimentRunService
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotCreate
from gws_core.io.io_spec_helper import InputSpecs
from gws_core.protocol.protocol_exception import ProtocolBuildException


#################### Error during the task ################
@task_decorator("ErrorTask")
class ErrorTask(Task):
    input_specs: InputSpecs = {'robot': InputSpec(Robot)}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        raise Exception("This is the error task")


@protocol_decorator("TestSubErrorProtocol")
class TestSubErrorProtocol(Protocol):
    def configure_protocol(self) -> None:
        create: ProcessSpec = self.add_process(RobotCreate, 'create')
        error: ProcessSpec = self.add_process(ErrorTask, 'error')

        self.add_connector(create >> 'robot', error << 'robot')


@protocol_decorator("TestErrorProtocol")
class TestErrorProtocol(Protocol):
    def configure_protocol(self) -> None:
        self.add_process(TestSubErrorProtocol, 'sub_proto')

############## Before task error ###################


@task_decorator("CheckBeforeTaskError")
class CheckBeforeTaskError(Task):
    def check_before_run(self, params: ConfigParams, inputs: TaskInputs) -> CheckBeforeTaskResult:
        return {"result": False, "message": "We can't run this task"}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        pass


@protocol_decorator("CheckBeforeTaskErrorProtocol")
class CheckBeforeTaskErrorProtocol(Protocol):
    def configure_protocol(self) -> None:
        self.add_process(CheckBeforeTaskError, 'error')

#################### Error on protocol build ###########################


@resource_decorator("NotRobot")
class NotRobot(Resource):
    pass


@task_decorator("NotRobotCreate")
class NotRobotCreate(Task):
    input_specs = {}
    output_specs = {'not_robot': OutputSpec(NotRobot)}
    config_specs = {}

    async def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {'not_robot': NotRobot()}


@protocol_decorator("TestSubProtocolBuildError")
class TestSubProtocolBuildError(Protocol):
    def configure_protocol(self) -> None:
        not_robot: ProcessSpec = self.add_process(NotRobotCreate, 'not_robot')
        move: ProcessSpec = self.add_process(RobotMove, 'move')

        self.add_connectors([
            (not_robot >> 'not_robot', move << 'robot')
        ])


@protocol_decorator("TestNestedProtocol")
class TestProtocolBuildError(Protocol):
    def configure_protocol(self) -> None:
        self.add_process(TestSubProtocolBuildError, 'sub_proto')


class TestProtocolError(BaseTestCase):

    async def test_error_on_task(self):
        """Test an experiment with a task that throws an exception """

        protocol: ProtocolModel = ProtocolService.create_protocol_model_from_type(TestErrorProtocol)

        experiment: Experiment = ExperimentService.create_experiment_from_protocol_model(protocol)

        # check that the experiment end up in error and get exception
        exception: ExperimentRunException
        try:
            await ExperimentRunService.run_experiment(experiment=experiment)
        except ExperimentRunException as err:
            exception = err
        else:
            self.fail('Run experiment shoud have raised ExperimentRunException')

        # Check that experiment is in error status
        experiment = ExperimentService.get_experiment_by_id(experiment.id)
        self.assertTrue(experiment.is_error)
        self.assertIsNotNone(experiment.error_info)
        # Check that the instance_id and unique_code where copied from base exception
        self.assertEqual(experiment.error_info['instance_id'], exception.instance_id)
        self.assertEqual(experiment.error_info['unique_code'], exception.unique_code)

        # Check that the context is correct
        self.assertEqual(experiment.error_info['context'], "Main protocol > sub_proto > error")

        # Check that main protocol is in error status
        protocol: ProtocolModel = experiment.protocol_model
        self.assertTrue(protocol.is_error)
        self.assertIsNotNone(protocol.error_info)
        self.assertEqual(protocol.error_info['instance_id'], exception.instance_id)
        self.assertEqual(protocol.error_info['unique_code'], exception.unique_code)

        # Check sub protocol is in error status
        sub_protocol: ProtocolModel = protocol.get_process('sub_proto')
        self.assertTrue(sub_protocol.is_error)
        self.assertIsNotNone(sub_protocol.error_info)
        self.assertEqual(sub_protocol.error_info['instance_id'], exception.instance_id)
        self.assertEqual(sub_protocol.error_info['unique_code'], exception.unique_code)

        # Check that the create process endup in success
        create_process: ProcessModel = sub_protocol.get_process('create')
        self.assertTrue(create_process.is_success)

        # Check that process is in error status
        error_process: ProcessModel = sub_protocol.get_process('error')
        self.assertTrue(error_process.is_error)
        self.assertIsNotNone(error_process.error_info)
        self.assertEqual(error_process.error_info['instance_id'], exception.instance_id)
        self.assertEqual(error_process.error_info['unique_code'], exception.unique_code)

    async def test_error_on_before_check(self):
        protocol: ProtocolModel = ProtocolService.create_protocol_model_from_type(CheckBeforeTaskErrorProtocol)

        experiment: Experiment = ExperimentService.create_experiment_from_protocol_model(protocol)

        # check that the experiment end up in error and get exception
        exception: ExperimentRunException
        try:
            await ExperimentRunService.run_experiment(experiment=experiment)
        except ExperimentRunException as err:
            exception = err
        else:
            self.fail('Run experiment shoud have raised ExperimentRunException')

        # Check that experiment is in error status
        experiment = ExperimentService.get_experiment_by_id(experiment.id)
        self.assertTrue(experiment.is_error)
        self.assertIsNotNone(experiment.error_info)
        # Check that the instance_id and unique_code where copied from base exception
        self.assertEqual(experiment.error_info['instance_id'], exception.instance_id)
        self.assertEqual(experiment.error_info['unique_code'], exception.unique_code)

        # Check that the context is correct
        self.assertEqual(experiment.error_info['context'], "Main protocol > error")

    def test_protocol_build_error(self):
        """Test an error happens during protocol build
        """
        exception: ProtocolBuildException
        try:
            ProcessFactory.create_protocol_model_from_type(TestProtocolBuildError)
        except ProtocolBuildException as err:
            exception = err
        else:
            self.fail('Run experiment shoud have raisedd ProtocolBuildException')
