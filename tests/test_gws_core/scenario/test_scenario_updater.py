import uuid

from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.impl.robot.robot_tasks import RobotCreate, RobotMove
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_builder import ScenarioBuilder
from gws_core.scenario.scenario_enums import ScenarioStatus
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.scenario_service import ScenarioService
from gws_core.scenario.scenario_zipper import ScenarioExportPackage
from gws_core.share.shared_dto import ShareEntityCreateMode
from gws_core.test.base_test_case import BaseTestCase
from gws_core.user.current_user_service import CurrentUserService


def _build_keep_id(
    scenario_package: ScenarioExportPackage,
    resource_zip_paths: dict[str, str] | None = None,
    skip_scenario_tags: bool = True,
) -> Scenario:
    """Build (or update) a scenario with ScenarioBuilder in KEEP_ID mode.

    Returns the built/updated scenario.
    """
    if resource_zip_paths is None:
        resource_zip_paths = {}

    current_user = CurrentUserService.get_and_check_current_user()
    origin = ExternalLabApiService.get_current_lab_info(current_user)

    builder = ScenarioBuilder(
        scenario_info=scenario_package,
        origin=origin,
        create_mode=ShareEntityCreateMode.KEEP_ID,
        skip_scenario_tags=skip_scenario_tags,
    )
    scenario = builder.build()
    builder.fill_zip_resources(resource_zip_paths)
    return scenario


def _export_with_remapped_ids(
    source_scenario: ScenarioProxy,
    target_scenario: ScenarioProxy,
    process_id_map: dict[str, str] | None = None,
) -> ScenarioExportPackage:
    """Export `source_scenario` and remap its IDs to match `target_scenario`.

    This is the cleanest way to build a ScenarioExportPackage that the updater
    can apply on top of `target_scenario`.

    Args:
        source_scenario: The scenario whose *structure* we want (the "new" state).
        target_scenario: The existing scenario we want to update.
        process_id_map: Optional mapping of source instance_name -> target process ID.
                        For every process whose instance_name appears in this map,
                        the exported node's ``id`` is replaced with the target's
                        real DB id so the updater treats it as an existing process
                        rather than a new one.
    """
    package = ScenarioService.export_scenario(source_scenario.get_model_id())

    # Remap scenario and protocol IDs to the target
    package.scenario.id = target_scenario.get_model_id()
    package.protocol.data.id = target_scenario.get_protocol().get_model_id()

    # Remap process IDs for processes that should be matched
    if process_id_map:
        for instance_name, target_id in process_id_map.items():
            node = package.protocol.data.graph.nodes.get(instance_name)
            if node:
                node.id = target_id

    return package


# test_scenario_updater
class TestScenarioUpdater(BaseTestCase):
    def test_update_scenario_remove_process(self):
        """Test that a process is removed when the update package does not contain it."""
        # Create scenario with: RobotCreate -> RobotMove
        scenario = ScenarioProxy()
        protocol = scenario.get_protocol()
        create = protocol.add_process(RobotCreate, "create")
        move = protocol.add_process(RobotMove, "move")
        protocol.add_connector(create >> "robot", move << "robot")
        scenario.run()

        # Build an update package with only the Create process
        source = ScenarioProxy()
        source_proto = source.get_protocol()
        source_proto.add_process(RobotCreate, "create")

        package = _export_with_remapped_ids(
            source_scenario=source,
            target_scenario=scenario,
            process_id_map={"create": create.get_model_id()},
        )

        updated = _build_keep_id(package)

        # Verify same scenario/protocol id and only Create remains
        protocol.refresh()
        self.assertEqual(scenario.get_model_id(), updated.id)
        self.assertEqual(protocol.get_model_id(), updated.protocol_model.id)
        self.assertEqual(create.get_model_id(), protocol.get_process("create").get_model_id())
        self.assertFalse(protocol.has_process("move"))

    def test_update_scenario_add_process(self):
        """Test that a new process is added when the update package contains an extra process."""
        # Create scenario with only RobotCreate
        scenario = ScenarioProxy()
        protocol = scenario.get_protocol()
        create = protocol.add_process(RobotCreate, "create")
        scenario.run()

        # Build an update package with RobotCreate -> RobotMove
        source = ScenarioProxy()
        source_proto = source.get_protocol()
        source_create = source_proto.add_process(RobotCreate, "create")
        source_move = source_proto.add_process(RobotMove, "move")
        source_proto.add_connector(source_create >> "robot", source_move << "robot")

        package = _export_with_remapped_ids(
            source_scenario=source,
            target_scenario=scenario,
            process_id_map={"create": create.get_model_id(), "move": str(uuid.uuid4())},
        )

        # Delete the source scenario before building so the new "move" process
        # doesn't conflict with the source's DB records (progress_bar unique constraint)
        # source.delete()

        updated = _build_keep_id(package)

        # Verify same scenario/protocol id and both processes exist
        protocol.refresh()
        self.assertEqual(scenario.get_model_id(), updated.id)
        self.assertEqual(protocol.get_model_id(), updated.protocol_model.id)
        self.assertEqual(create.get_model_id(), protocol.get_process("create").get_model_id())
        self.assertTrue(protocol.has_process("move"))

    def test_update_draft_to_run_scenario(self):
        """Test updating a draft (not run) scenario to a run (SUCCESS) scenario."""
        # Create a draft scenario with RobotCreate -> RobotMove (do NOT run it)
        scenario = ScenarioProxy()
        protocol = scenario.get_protocol()
        create = protocol.add_process(RobotCreate, "create")
        move = protocol.add_process(RobotMove, "move")
        protocol.add_connector(create >> "robot", move << "robot")
        # scenario is in DRAFT status

        # Build a "run" source scenario with same structure
        source = ScenarioProxy()
        source_proto = source.get_protocol()
        source_create = source_proto.add_process(RobotCreate, "create")
        source_move = source_proto.add_process(RobotMove, "move")
        source_proto.add_connector(source_create >> "robot", source_move << "robot")
        source.run()

        package = _export_with_remapped_ids(
            source_scenario=source,
            target_scenario=scenario,
            process_id_map={
                "create": create.get_model_id(),
                "move": move.get_model_id(),
            },
        )

        updated = _build_keep_id(package)

        # Verify the scenario is now SUCCESS
        self.assertEqual(scenario.get_model_id(), updated.id)
        self.assertEqual(updated.status, ScenarioStatus.SUCCESS)

        # Verify both processes exist and were updated
        protocol.refresh()
        self.assertTrue(protocol.has_process("create"))
        self.assertTrue(protocol.has_process("move"))

    def test_update_scenario_rerun_single_task(self):
        """Test that re-running a single task in the source resets it in the target."""
        # Create and run scenario with RobotCreate -> RobotMove
        scenario = ScenarioProxy()
        protocol = scenario.get_protocol()
        create = protocol.add_process(RobotCreate, "create")
        move = protocol.add_process(RobotMove, "move")
        protocol.add_connector(create >> "robot", move << "robot")
        scenario.run()

        # Record original output resource id of "move"
        move.refresh()
        original_move_output = move.get_model().outputs.ports["robot"].get_resource_model_id()
        self.assertIsNotNone(original_move_output)

        # Build a source scenario, run it, then re-run just the "move" task
        # so that the "move" output resource id changes but "create" stays the same
        source = ScenarioProxy()
        source_proto = source.get_protocol()
        source_create = source_proto.add_process(RobotCreate, "create")
        source_move = source_proto.add_process(RobotMove, "move")
        source_proto.add_connector(source_create >> "robot", source_move << "robot")
        source.run()

        # Reset and re-run only the "move" process to get a new output resource id
        source_move.reset_process()
        source.run()

        source_move.refresh()
        source_move_output = source_move.get_model().outputs.ports["robot"].get_resource_model_id()
        # The source move should have a different output than the original
        self.assertIsNotNone(source_move_output)

        package = _export_with_remapped_ids(
            source_scenario=source,
            target_scenario=scenario,
            process_id_map={
                "create": create.get_model_id(),
                "move": move.get_model_id(),
            },
        )

        updated = _build_keep_id(package)

        # After update, the "move" process should have been detected as rerun
        # and its outputs should have been reset (cleared)
        protocol.refresh()
        move.refresh()
        self.assertEqual(scenario.get_model_id(), updated.id)
        self.assertTrue(protocol.has_process("create"))
        self.assertTrue(protocol.has_process("move"))

        # The move process should have been reset — its output resource should be gone
        updated_move = protocol.get_process("move")
        updated_move_output = (
            updated_move.get_model().outputs.ports["robot"].get_resource_model_id()
        )
        self.assertNotEqual(updated_move_output, original_move_output)
