from gws_core import (
    BaseTestCase,
    ProcessFactory,
    ProtocolModel,
    ScenarioProxy,
    Table,
    TaskModel,
)
from gws_core.config.param.dynamic_param import DynamicParam
from gws_core.config.param.param_spec import IntParam
from gws_core.impl.agent.py_agent import PyAgent
from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotCreate, RobotMove
from gws_core.io.io_spec import IOSpecDTO
from gws_core.model.typing import Typing
from gws_core.process.process_types import ProcessStatus
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.task.plug.input_task import InputTask

from ..protocol_examples import TestNestedProtocol, TestSimpleProtocol


# test_process_factory
class TestProcessFactory(BaseTestCase):
    # ======================== TASK MODEL CREATION ========================

    def test_create_task_model_from_type(self):
        """Test creating a task model from a task type."""
        # Default parameters
        task_model: TaskModel = ProcessFactory.create_task_model_from_type(task_type=RobotCreate)
        self.assertIsInstance(task_model, TaskModel)
        self.assertIsNotNone(task_model.id)
        self.assertEqual(task_model.status, ProcessStatus.DRAFT)
        self.assertIsNotNone(task_model.config)
        self.assertIsNotNone(task_model.progress_bar)
        self.assertEqual(task_model.instance_name, task_model.id)

        # With instance_name and name
        task_model = ProcessFactory.create_task_model_from_type(
            task_type=RobotCreate, instance_name="my_robot_creator", name="My Robot Creator"
        )
        self.assertEqual(task_model.instance_name, "my_robot_creator")
        self.assertEqual(task_model.name, "My Robot Creator")

        # With config params
        task_model = ProcessFactory.create_task_model_from_type(
            task_type=RobotMove, config_params={"moving_step": 0.5, "direction": "south"}
        )
        self.assertEqual(task_model.config.get_value("moving_step"), 0.5)
        self.assertEqual(task_model.config.get_value("direction"), "south")

        # Check that input and output ports are created from specs
        # RobotMove has input 'robot' and outputs 'robot' and 'food'
        self.assertIn("robot", task_model.inputs.get_port_names())
        self.assertIn("robot", task_model.outputs.get_port_names())
        self.assertIn("food", task_model.outputs.get_port_names())

    def test_create_task_model_with_invalid_config_params(self):
        """Test that invalid config params raise an exception."""
        with self.assertRaises(Exception):
            ProcessFactory.create_task_model_from_type(
                task_type=RobotMove, config_params={"nonexistent_param": "value"}
            )

    # ======================== TASK MODEL FROM TYPING NAME ========================

    def test_create_task_model_from_typing_name(self):
        """Test creating a task model from a typing name."""
        task_model = ProcessFactory.create_task_model_from_typing_name(
            typing_name=RobotCreate.get_typing_name()
        )
        self.assertIsInstance(task_model, TaskModel)

    def test_create_task_model_from_typing_name_with_params(self):
        """Test creating a task model from typing name with config params."""
        task_model = ProcessFactory.create_task_model_from_typing_name(
            typing_name=RobotMove.get_typing_name(),
            config_params={"moving_step": 0.3},
            instance_name="move_task",
        )
        self.assertEqual(task_model.config.get_value("moving_step"), 0.3)
        self.assertEqual(task_model.instance_name, "move_task")

    # ======================== PROTOCOL MODEL CREATION ========================

    def test_create_protocol_model_from_type(self):
        """Test creating a protocol model from a protocol type."""
        # Default parameters
        protocol_model = ProcessFactory.create_protocol_model_from_type(
            protocol_type=TestSimpleProtocol
        )
        self.assertIsInstance(protocol_model, ProtocolModel)
        self.assertIsNotNone(protocol_model.id)
        self.assertEqual(protocol_model.status, ProcessStatus.DRAFT)

        # Check that processes are created
        process_names = set(protocol_model.processes.keys())
        expected = {"p0", "p1", "p2", "p3", "p4", "p5", "p_wait"}
        self.assertEqual(process_names, expected)

        # With instance_name and name
        protocol_model = ProcessFactory.create_protocol_model_from_type(
            protocol_type=TestSimpleProtocol, instance_name="my_protocol", name="My Protocol"
        )
        self.assertEqual(protocol_model.instance_name, "my_protocol")
        self.assertEqual(protocol_model.name, "My Protocol")

    def test_create_nested_protocol(self):
        """Test creating a protocol that contains a sub-protocol."""
        protocol_model = ProcessFactory.create_protocol_model_from_type(
            protocol_type=TestNestedProtocol
        )
        self.assertIsInstance(protocol_model, ProtocolModel)
        process_names = set(protocol_model.processes.keys())
        self.assertIn("p0", process_names)
        self.assertIn("p5", process_names)
        self.assertIn("mini_proto", process_names)

    # ======================== EMPTY PROTOCOL ========================

    def test_create_protocol_empty(self):
        """Test creating an empty protocol model."""
        protocol_model = ProcessFactory.create_protocol_empty()
        self.assertIsInstance(protocol_model, ProtocolModel)
        self.assertEqual(protocol_model.status, ProcessStatus.DRAFT)
        self.assertIsNotNone(protocol_model.id)

        # With instance_name and name
        protocol_model = ProcessFactory.create_protocol_empty(
            instance_name="empty_proto", name="Empty Protocol"
        )
        self.assertEqual(protocol_model.instance_name, "empty_proto")
        self.assertEqual(protocol_model.name, "Empty Protocol")

    # ======================== PROCESS MODEL (GENERIC) ========================

    def test_create_process_model_from_type_task(self):
        """Test that create_process_model_from_type dispatches correctly for Task types."""
        task_model = ProcessFactory.create_process_model_from_type(process_type=RobotCreate)
        self.assertIsInstance(task_model, TaskModel)

    def test_create_process_model_from_type_protocol(self):
        """Test that create_process_model_from_type dispatches correctly for Protocol types."""
        process_model = ProcessFactory.create_process_model_from_type(
            process_type=TestSimpleProtocol
        )
        self.assertIsNotNone(process_model)

    def test_create_process_model_from_typing_name(self):
        """Test creating a process model from a typing name."""
        task_model = ProcessFactory.create_process_model_from_typing_name(
            typing_name=RobotCreate.get_typing_name()
        )
        self.assertIsInstance(task_model, TaskModel)

    # ======================== SPECIFIC FACTORY METHODS ========================

    def test_create_source(self):
        """Test creating a source (InputTask) model."""
        robot_model = ResourceModel.save_from_resource(
            Robot.empty(), origin=ResourceOrigin.UPLOADED
        )
        task_model = ProcessFactory.create_source(resource_id=robot_model.id)
        self.assertIsInstance(task_model, TaskModel)
        self.assertEqual(task_model.config.get_value(InputTask.config_name), robot_model.id)

    def test_create_output_task(self):
        """Test creating an OutputTask model."""
        task_model = ProcessFactory.create_output_task()
        self.assertIsInstance(task_model, TaskModel)

    def test_create_viewer(self):
        """Test creating a Viewer task model."""
        task_model = ProcessFactory.create_viewer(resource_typing_name=Robot.get_typing_name())
        self.assertIsInstance(task_model, TaskModel)

    # ======================== DYNAMIC IO ========================

    def test_create_task_model_with_dynamic_io(self):
        """Test that a task with dynamic ports is correctly recreated from ProcessConfigDTO."""
        scenario = ScenarioProxy()
        protocol = scenario.get_protocol()
        agent = protocol.add_process(PyAgent, "agent")

        # Add dynamic input (Table) and output (Robot) ports
        table_typing = Typing.get_by_model_type(Table)
        new_input_port = agent.add_dynamic_input_port(port_spec_dto=IOSpecDTO(
            resource_types=[table_typing.to_ref_dto()], optional=False,
        ))

        robot_typing = Typing.get_by_model_type(Robot)
        new_output_port = agent.add_dynamic_output_port(port_spec_dto=IOSpecDTO(
            resource_types=[robot_typing.to_ref_dto()], optional=False,
        ))

        # Export to ProcessConfigDTO and recreate via factory
        agent_model = agent.get_model()
        config_dto = agent_model.to_config_dto()
        recreated_model = ProcessFactory.create_task_model_from_config_dto(config_dto)

        # Verify the recreated model has the dynamic ports with correct types
        self.assertIsInstance(recreated_model, TaskModel)
        self.assertEqual(recreated_model.id, agent_model.id)

        self.assertIn(new_input_port.port_name, recreated_model.inputs.get_port_names())
        self.assertIn(new_output_port.port_name, recreated_model.outputs.get_port_names())

    # ======================== DYNAMIC CONFIG ========================

    def test_create_task_model_with_dynamic_config(self):
        """Test that a task with dynamic config params is correctly recreated from ProcessConfigDTO."""
        scenario = ScenarioProxy()
        protocol = scenario.get_protocol()
        agent = protocol.add_process(PyAgent, "agent")

        # Add a dynamic param
        agent.add_dynamic_param(
            PyAgent.CONFIG_PARAMS_NAME,
            "my_int",
            IntParam(default_value=10, optional=True).to_dto(),
        )

        # Export to ProcessConfigDTO and recreate via factory
        agent_model = agent.get_model()
        config_dto = agent_model.to_config_dto()
        recreated_model = ProcessFactory.create_task_model_from_config_dto(config_dto)

        # Verify the recreated model has the dynamic param with correct value
        self.assertIsInstance(recreated_model, TaskModel)
        dynamic_param: DynamicParam = recreated_model.config.get_spec(PyAgent.CONFIG_PARAMS_NAME)
        self.assertIsInstance(dynamic_param, DynamicParam)
        self.assertTrue(dynamic_param.specs.has_spec("my_int"))
        self.assertEqual(
            recreated_model.config.get_value(PyAgent.CONFIG_PARAMS_NAME)["my_int"], 10
        )
