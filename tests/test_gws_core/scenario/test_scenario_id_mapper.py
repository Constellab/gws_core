from typing import cast

from gws_core.impl.robot.robot_resource import Robot
from gws_core.impl.robot.robot_tasks import RobotMove
from gws_core.resource.resource_dto import ResourceOrigin
from gws_core.resource.resource_model import ResourceModel
from gws_core.scenario.scenario_enums import ScenarioStatus
from gws_core.scenario.scenario_id_mapper import ScenarioIdMapper
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.share.shared_dto import ShareEntityCreateMode
from gws_core.task.plug.input_task import InputTask
from gws_core.task.task_model import TaskModel
from gws_core.test.base_test_case import BaseTestCase


# test_scenario_id_mapper
class TestScenarioIdMapper(BaseTestCase):
    def test_apply_new_ids(self):
        """Test the full apply_new_ids flow: export, load, apply mapper, verify all IDs changed.
        Also verifies that InputTask config resource_id is updated."""
        # Create a robot resource manually
        robot = Robot.empty()
        original_robot_source = ResourceModel.save_from_resource(
            robot, origin=ResourceOrigin.UPLOADED
        )

        # Create and run a scenario with an InputTask feeding into RobotMove
        scenario = ScenarioProxy(title="Integration test")
        protocol = scenario.get_protocol()
        move = protocol.add_process(RobotMove, "move")
        protocol.add_source("robot_source", original_robot_source.id, move << "robot")
        scenario.run()
        scenario.refresh()

        scenario_model = scenario.get_model()
        self.assertEqual(scenario_model.status, ScenarioStatus.SUCCESS)

        # Capture original IDs
        protocol_model = scenario_model.protocol_model
        original_scenario_id = scenario_model.id
        original_protocol_id = protocol_model.id
        resource_models = protocol_model.get_input_and_output_resource_models()
        original_process_ids = {
            name: process.id for name, process in protocol_model.processes.items()
        }

        # Store original output port resource IDs for robot_source (InputTask) and move processes
        move_process_model = protocol_model.get_process("move")
        original_move_robot_id = move_process_model.out_port("robot").get_resource_model_id()
        original_move_input_robot_id = move_process_model.in_port("robot").get_resource_model_id()

        # Apply the mapper (single call)
        mapper = ScenarioIdMapper(ShareEntityCreateMode.NEW_ID)
        mapper.apply_new_ids(
            protocol_model,
            resource_models,
            scenario_model,
        )

        # Verify scenario ID changed
        self.assertNotEqual(scenario_model.id, original_scenario_id)
        self.assertEqual(mapper.get_new_id(original_scenario_id), scenario_model.id)

        # Verify protocol ID changed
        self.assertNotEqual(protocol_model.id, original_protocol_id)
        self.assertEqual(mapper.get_new_id(original_protocol_id), protocol_model.id)
        # Verify protocol.scenario_id updated
        self.assertEqual(mapper.get_new_id(original_scenario_id), protocol_model.scenario.id)

        # Verify protocol progress_bar.process_id updated
        self.assertEqual(protocol_model.progress_bar.process_id, protocol_model.id)

        # Verify all process IDs changed and progress_bar.process_id updated
        for name, original_id in original_process_ids.items():
            process = protocol_model.get_process(name)
            self.assertNotEqual(process.id, original_id)
            self.assertEqual(mapper.get_new_id(original_id), process.id)
            self.assertEqual(process.progress_bar.process_id, process.id)

        # Verify port resource IDs were updated for robot_source and move processes
        source_process = cast(TaskModel, protocol_model.get_process("robot_source"))
        move_process = protocol_model.get_process("move")

        # Check robot_source (InputTask) output port
        source_robot_port = source_process.out_port(InputTask.output_name)
        self.assertNotEqual(source_robot_port.get_resource_model_id(), original_robot_source.id)
        self.assertEqual(
            source_robot_port.get_resource_model_id(), mapper.get_new_id(original_robot_source.id)
        )
        source_resource_model = source_robot_port.get_resource_model()
        self.assertIsNone(source_resource_model.scenario)
        self.assertIsNone(source_resource_model.task_model)

        # Check move process input port
        move_input_robot_port = move_process.in_port("robot")
        self.assertNotEqual(
            move_input_robot_port.get_resource_model_id(), original_move_input_robot_id
        )
        self.assertEqual(
            move_input_robot_port.get_resource_model_id(),
            mapper.get_new_id(original_move_input_robot_id),
        )

        # Check move process output port
        move_robot_port = move_process.out_port("robot")
        self.assertNotEqual(move_robot_port.get_resource_model_id(), original_move_robot_id)
        self.assertEqual(
            move_robot_port.get_resource_model_id(), mapper.get_new_id(original_move_robot_id)
        )
        move_resource_model = move_robot_port.get_resource_model()
        self.assertEqual(move_resource_model.scenario.id, scenario_model.id)
        self.assertEqual(move_resource_model.task_model.id, move_process.id)

        # Verify InputTask config resource_id was updated
        new_config_resource_id = source_process.config.get_value(InputTask.config_name)
        self.assertIsNotNone(new_config_resource_id)
        self.assertNotEqual(new_config_resource_id, original_robot_source.id)
        self.assertEqual(new_config_resource_id, mapper.get_new_id(original_robot_source.id))

        # Verify task model source_config_id updated for InputTask
        self.assertEqual(
            source_process.source_config_id, mapper.get_new_id(original_robot_source.id)
        )

    def test_apply_keep_ids(self):
        """Test apply_new_ids with KEEP_ID mode: all IDs should remain unchanged."""
        # Create a robot resource manually
        robot = Robot.empty()
        original_robot_source = ResourceModel.save_from_resource(
            robot, origin=ResourceOrigin.UPLOADED
        )

        # Create and run a scenario with an InputTask feeding into RobotMove
        scenario = ScenarioProxy(title="Keep ID test")
        protocol = scenario.get_protocol()
        move = protocol.add_process(RobotMove, "move")
        protocol.add_source("robot_source", original_robot_source.id, move << "robot")
        scenario.run()
        scenario.refresh()

        scenario_model = scenario.get_model()
        self.assertEqual(scenario_model.status, ScenarioStatus.SUCCESS)

        # Capture original IDs
        protocol_model = scenario_model.protocol_model
        original_scenario_id = scenario_model.id
        original_protocol_id = protocol_model.id
        resource_models = protocol_model.get_input_and_output_resource_models()
        original_process_ids = {
            name: process.id for name, process in protocol_model.processes.items()
        }
        original_resource_ids = {model.id for model in resource_models}

        # Store original port resource IDs
        move_process_model = protocol_model.get_process("move")
        original_move_robot_id = move_process_model.out_port("robot").get_resource_model_id()
        original_move_input_robot_id = move_process_model.in_port("robot").get_resource_model_id()

        # Apply the mapper with KEEP_ID mode
        mapper = ScenarioIdMapper(ShareEntityCreateMode.KEEP_ID)
        mapper.apply_new_ids(
            protocol_model,
            resource_models,
            scenario_model,
        )

        # Verify scenario ID unchanged
        self.assertEqual(scenario_model.id, original_scenario_id)

        # Verify protocol ID unchanged
        self.assertEqual(protocol_model.id, original_protocol_id)
        self.assertEqual(protocol_model.scenario.id, original_scenario_id)

        # Verify protocol progress_bar.process_id unchanged
        self.assertEqual(protocol_model.progress_bar.process_id, protocol_model.id)

        # Verify all process IDs unchanged
        for name, original_id in original_process_ids.items():
            process = protocol_model.get_process(name)
            self.assertEqual(process.id, original_id)
            self.assertEqual(process.progress_bar.process_id, process.id)

        # Verify resource IDs unchanged
        current_resource_ids = {model.id for model in resource_models}
        self.assertEqual(current_resource_ids, original_resource_ids)

        # Verify port resource IDs unchanged
        source_process = cast(TaskModel, protocol_model.get_process("robot_source"))
        move_process = protocol_model.get_process("move")

        source_robot_port = source_process.out_port(InputTask.output_name)
        self.assertEqual(source_robot_port.get_resource_model_id(), original_robot_source.id)

        move_input_robot_port = move_process.in_port("robot")
        self.assertEqual(move_input_robot_port.get_resource_model_id(), original_move_input_robot_id)

        move_robot_port = move_process.out_port("robot")
        self.assertEqual(move_robot_port.get_resource_model_id(), original_move_robot_id)

        # Verify InputTask config resource_id unchanged
        config_resource_id = source_process.config.get_value(InputTask.config_name)
        self.assertEqual(config_resource_id, original_robot_source.id)
