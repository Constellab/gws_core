

from gws_core import (BaseTestCase, CheckBeforeTaskResult, ConfigParams,
                      InputSpec, InputSpecs, OutputSpec, OutputSpecs,
                      ProcessFactory, ProcessModel, ProcessSpec, Protocol,
                      ProtocolModel, ProtocolService, Resource,
                      ScenarioService, Task, TaskInputs, TaskOutputs,
                      protocol_decorator, resource_decorator, task_decorator)
from gws_core.config.config_specs import ConfigSpecs
from gws_core.entity_navigator.entity_navigator_service import \
    EntityNavigatorService
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotCreate, RobotMove
from gws_core.protocol.protocol_exception import ProtocolBuildException
from gws_core.scenario.scenario_exception import ScenarioRunException
from gws_core.scenario.scenario_run_service import ScenarioRunService

#################### Error during the task ################


@task_decorator("ErrorTask")
class ErrorTask(Task):
    input_specs: InputSpecs = InputSpecs({'robot': InputSpec(Robot)})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        raise Exception("This is the error task")


@protocol_decorator("TestSubErrorProtocol", human_name='TestSurbErrorProtocol')
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

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
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
    output_specs = OutputSpecs({'not_robot': OutputSpec(NotRobot)})
    config_specs = ConfigSpecs({})

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        return {'not_robot': NotRobot()}


@protocol_decorator("TestSubProtocolBuildError")
class TestSubProtocolBuildError(Protocol):
    def configure_protocol(self) -> None:
        not_robot: ProcessSpec = self.add_process(NotRobotCreate, 'not_robot')
        move: ProcessSpec = self.add_process(RobotMove, 'move')

        self.add_connectors([
            (not_robot >> 'not_robot', move << 'robot')
        ])


@protocol_decorator("TestProtocolBuildError")
class TestProtocolBuildError(Protocol):
    def configure_protocol(self) -> None:
        self.add_process(TestSubProtocolBuildError, 'sub_proto')


# test_protocol_error
class TestProtocolError(BaseTestCase):

    def test_error_on_task(self):
        """Test a scenario with a task that throws an exception """

        protocol = ProtocolService.create_protocol_model_from_type(
            TestErrorProtocol)

        scenario = ScenarioService.create_scenario_from_protocol_model(
            protocol)

        # check that the scenario end up in error and get exception
        exception: ScenarioRunException
        try:
            ScenarioRunService.run_scenario(scenario=scenario)
        except ScenarioRunException as err:
            exception = err
        else:
            self.fail('Run scenario shoud have raised ScenarioRunException')

        # Check that scenario is in error status
        scenario = ScenarioService.get_by_id_and_check(scenario.id)
        self.assertTrue(scenario.is_error)
        self.assertIsNotNone(scenario.get_error_info())
        # Check that the instance_id and unique_code where copied from base exception
        self.assertEqual(
            scenario.get_error_info().instance_id, exception.instance_id)
        self.assertEqual(
            scenario.get_error_info().unique_code, exception.unique_code)

        # Check that main protocol is in error status
        protocol = scenario.protocol_model
        self.assertTrue(protocol.is_error)
        self.assertIsNotNone(protocol.get_error_info())
        self.assertEqual(
            protocol.get_error_info().instance_id, exception.instance_id)
        self.assertEqual(
            protocol.get_error_info().unique_code, exception.unique_code)

        # Check sub protocol is in error status
        sub_protocol: ProtocolModel = protocol.get_process('sub_proto')
        self.assertTrue(sub_protocol.is_error)
        self.assertIsNotNone(sub_protocol.get_error_info())
        self.assertEqual(
            sub_protocol.get_error_info().instance_id, exception.instance_id)
        self.assertEqual(
            sub_protocol.get_error_info().unique_code, exception.unique_code)

        # Check that the create process endup in success
        create_process: ProcessModel = sub_protocol.get_process('create')
        self.assertTrue(create_process.is_success)

        # Check that process is in error status
        error_process: ProcessModel = sub_protocol.get_process('error')
        self.assertTrue(error_process.is_error)
        self.assertIsNotNone(error_process.get_error_info())
        self.assertEqual(
            error_process.get_error_info().instance_id, exception.instance_id)
        self.assertEqual(
            error_process.get_error_info().unique_code, exception.unique_code)

        # reset error tasks
        EntityNavigatorService.reset_error_processes_of_protocol(protocol)

        protocol = protocol.refresh()
        self.assertTrue(protocol.is_partially_run)
        sub_protocol = sub_protocol.refresh()
        self.assertTrue(sub_protocol.is_partially_run)
        create_process = create_process.refresh()
        self.assertTrue(create_process.is_success)
        error_process = error_process.refresh()
        self.assertTrue(error_process.is_draft)

    def test_error_on_before_check(self):
        protocol = ProtocolService.create_protocol_model_from_type(
            CheckBeforeTaskErrorProtocol)

        scenario = ScenarioService.create_scenario_from_protocol_model(
            protocol)

        # check that the scenario end up in error and get exception
        exception: ScenarioRunException
        try:
            ScenarioRunService.run_scenario(scenario=scenario)
        except ScenarioRunException as err:
            exception = err
        else:
            self.fail('Run scenario shoud have raised ScenarioRunException')

        # Check that scenario is in error status
        scenario = ScenarioService.get_by_id_and_check(scenario.id)
        self.assertTrue(scenario.is_error)
        self.assertIsNotNone(scenario.error_info)
        # Check that the instance_id and unique_code where copied from base exception
        self.assertEqual(
            scenario.error_info['instance_id'], exception.instance_id)
        self.assertEqual(
            scenario.error_info['unique_code'], exception.unique_code)

    def test_protocol_build_error(self):
        """Test an error happens during protocol build
        """
        try:
            ProcessFactory.create_protocol_model_from_type(
                TestProtocolBuildError)
        except ProtocolBuildException:
            pass
        else:
            self.fail('Run scenario shoud have raisedd ProtocolBuildException')
