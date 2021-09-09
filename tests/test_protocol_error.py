# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


from gws_core import (BaseTestCase, CheckBeforeTaskResult, ConfigParams,
                      Experiment, ExperimentService, GTest, Process,
                      ProcessableModel, ProcessInputs, ProcessOutputs,
                      Protocol, ProtocolModel, ProtocolService,
                      process_decorator, protocol_decorator)
from gws_core.experiment.experiment_exception import ExperimentRunException
from gws_core.processable.processable_exception import \
    ProcessableCheckBeforeTaskStopException


@process_decorator("ErrorProcess")
class ErrorProcess(Process):
    async def task(self, config: ConfigParams, inputs: ProcessInputs) -> ProcessOutputs:
        raise Exception("This is the error process")


@protocol_decorator("TestSubProtocolError")
class TestSubProtocolError(Protocol):
    def configure_protocol(self, config_params: ConfigParams) -> None:
        self.add_process(ErrorProcess, 'error')


@protocol_decorator("TestProtocolError")
class TestProtocolError(Protocol):
    def configure_protocol(self, config_params: ConfigParams) -> None:
        self.add_process(TestSubProtocolError, 'sub_proto')


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


class TestProtocol(BaseTestCase):

    async def test_error_on_process(self):
        """Test an experiment with a process that throws an exception. Test that """
        GTest.print("Error Process")

        protocol: ProtocolModel = ProtocolService.create_protocol_model_from_type(TestProtocolError)

        experiment: Experiment = ExperimentService.create_experiment_from_protocol_model(protocol)

        # check that the experiment end up in error and get exception
        exception: ExperimentRunException
        try:
            await ExperimentService.run_experiment(experiment=experiment)
        except ExperimentRunException as err:
            exception = err
        else:
            self.fail('Run experiment shoud have raise aExperimentRunException ')

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
            self.fail('Run experiment shoud have raise aExperimentRunException ')

        # Check that experiment is in error status
        experiment = ExperimentService.get_experiment_by_uri(experiment.uri)
        self.assertTrue(experiment.is_error)
        self.assertIsNotNone(experiment.error_info)
        # Check that the instance_id and unique_code where copied from base exception
        self.assertEqual(experiment.error_info['instance_id'], exception.instance_id)
        self.assertEqual(experiment.error_info['unique_code'], exception.unique_code)

        # Check that the context is correct
        self.assertEqual(experiment.error_info['context'], "Main protocol > error")
