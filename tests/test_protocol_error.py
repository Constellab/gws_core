# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import (BaseTestCase, CheckBeforeTaskResult, ConfigParams,
                      Experiment, ExperimentService, GTest, Process,
                      ProcessableFactory, ProcessableModel, ProcessableSpec,
                      ProcessInputs, ProcessOutputs, Protocol, ProtocolModel,
                      ProtocolService, Resource, RobotMove, process_decorator,
                      protocol_decorator, resource_decorator)
from gws_core.experiment.experiment_exception import ExperimentRunException
from gws_core.protocol.protocol_exception import ProtocolBuildException


#################### Error during the process task ################
@process_decorator("ErrorProcess")
class ErrorProcess(Process):
    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        raise Exception("This is the error process")


@protocol_decorator("TestSubErrorProtocol")
class TestSubErrorProtocol(Protocol):
    def configure_protocol(self, config_params: ConfigParams) -> None:
        self.add_process(ErrorProcess, 'error')


@protocol_decorator("TestErrorProtocol")
class TestErrorProtocol(Protocol):
    def configure_protocol(self, config_params: ConfigParams) -> None:
        self.add_process(TestSubErrorProtocol, 'sub_proto')

############## Before task error ###################


@process_decorator("CheckBeforeTaskError")
class CheckBeforeTaskError(Process):
    def check_before_task(self, config: ConfigParams, inputs: ProcessInputs) -> CheckBeforeTaskResult:
        return {"result": False, "message": "We can't run this process"}

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        pass


@protocol_decorator("CheckBeforeTaskErrorProtocol")
class CheckBeforeTaskErrorProtocol(Protocol):
    def configure_protocol(self, config_params: ConfigParams) -> None:
        self.add_process(CheckBeforeTaskError, 'error')

#################### Error on protocol build ###########################


@resource_decorator("NotRobot")
class NotRobot(Resource):
    pass


@process_decorator("NotRobotCreate")
class NotRobotCreate(Process):
    input_specs = {}
    output_specs = {'not_robot': NotRobot}
    config_specs = {}

    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        return {'not_robot': NotRobot()}


@protocol_decorator("TestSubProtocolBuildError")
class TestSubProtocolBuildError(Protocol):
    def configure_protocol(self, config_params: ConfigParams) -> None:
        not_robot: ProcessableSpec = self.add_process(NotRobotCreate, 'not_robot')
        move: ProcessableSpec = self.add_process(RobotMove, 'move')

        self.add_connectors([
            (not_robot >> 'not_robot', move << 'robot')
        ])


@protocol_decorator("TestNestedProtocol")
class TestProtocolBuildError(Protocol):
    def configure_protocol(self, config_params: ConfigParams) -> None:
        sub_proto: ProcessableSpec = self.add_process(TestSubProtocolBuildError, 'sub_proto')


class TestProtocolError(BaseTestCase):

    async def test_error_on_process(self):
        """Test an experiment with a process that throws an exception. Test that """
        GTest.print("Error Process")

        protocol: ProtocolModel = ProtocolService.create_protocol_model_from_type(TestErrorProtocol)

        experiment: Experiment = ExperimentService.create_experiment_from_protocol_model(protocol)

        # check that the experiment end up in error and get exception
        exception: ExperimentRunException
        try:
            await ExperimentService.run_experiment(experiment=experiment)
        except ExperimentRunException as err:
            exception = err
        else:
            self.fail('Run experiment shoud have raise ExperimentRunException ')

        print(exception)
        # Check that experiment is in error status
        experiment = ExperimentService.get_experiment_by_uri(experiment.uri)
        self.assertTrue(experiment.is_error)
        self.assertIsNotNone(experiment.error_info)
        # Check that the instance_id and unique_code where copied from base exception
        self.assertEqual(experiment.error_info['instance_id'], exception.instance_id)
        self.assertEqual(experiment.error_info['unique_code'], exception.unique_code)

        # Check that the context is correct
        self.assertEqual(experiment.error_info['context'], "Main protocol > sub_proto > error")

        # Check that main protocol is in error status
        protocol: ProtocolModel = experiment.protocol
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

        # Check that process is in error status
        sub_process: ProcessableModel = sub_protocol.get_process('error')
        self.assertTrue(sub_process.is_error)
        self.assertIsNotNone(sub_process.error_info)
        self.assertEqual(sub_process.error_info['instance_id'], exception.instance_id)
        self.assertEqual(sub_process.error_info['unique_code'], exception.unique_code)

    async def test_error_on_before_check(self):
        protocol: ProtocolModel = ProtocolService.create_protocol_model_from_type(CheckBeforeTaskErrorProtocol)

        experiment: Experiment = ExperimentService.create_experiment_from_protocol_model(protocol)

        # check that the experiment end up in error and get exception
        exception: ExperimentRunException
        try:
            await ExperimentService.run_experiment(experiment=experiment)
        except ExperimentRunException as err:
            exception = err
        else:
            self.fail('Run experiment shoud have raise ExperimentRunException ')

        # Check that experiment is in error status
        experiment = ExperimentService.get_experiment_by_uri(experiment.uri)
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
            ProcessableFactory.create_protocol_model_from_type(TestProtocolBuildError)
        except ProtocolBuildException as err:
            exception = err
        else:
            self.fail('Run experiment shoud have raise ProtocolBuildException ')

        print(exception)
