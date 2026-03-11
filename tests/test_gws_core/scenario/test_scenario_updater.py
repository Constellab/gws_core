from gws_core.folder.space_folder import SpaceFolder
from gws_core.impl.robot.robot_tasks import RobotCreate, RobotMove
from gws_core.resource.resource_model import ResourceModel
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_enums import ScenarioStatus
from gws_core.scenario.scenario_loader import ScenarioLoader
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.scenario_service import ScenarioService
from gws_core.scenario.scenario_updater import ScenarioUpdater
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import Tag, TagOrigins
from gws_core.tag.tag_dto import TagOriginType
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.test.base_test_case import BaseTestCase


def _make_tag(key: str, value: str, propagable: bool = False) -> Tag:
    """Helper to create a Tag with a USER origin."""
    return Tag(key, value, is_propagable=propagable, origins=TagOrigins(TagOriginType.USER, "test"))


# test_scenario_updater
class TestScenarioUpdater(BaseTestCase):
    def test_update_scenario_metadata(self):
        """Test that scenario metadata (title, description, status, folder) is updated."""
        # Create an initial scenario
        scenario_1 = ScenarioProxy(title="Original title")
        scenario_1_model = scenario_1.get_model()

        # Create a second scenario with different metadata
        folder = SpaceFolder(title="Updated folder")
        folder.save()
        scenario_2 = ScenarioProxy(title="Updated title", folder=folder)
        protocol_2 = scenario_2.get_protocol()
        protocol_2.add_process(RobotCreate, "create")
        scenario_2_model = scenario_2.get_model()

        zip_info = ScenarioService.export_scenario(scenario_2_model.id)
        loader = ScenarioLoader(zip_info)
        loader.load_scenario()

        updater = ScenarioUpdater(scenario_1_model, loader)
        updated = updater.update_scenario(skip_tags=True)

        self.assertEqual(updated.id, scenario_1_model.id)
        self.assertEqual(updated.title, "Updated title")
        self.assertEqual(updated.folder.id, folder.id)

    def test_update_scenario_with_processes(self):
        """Test that the protocol diff correctly updates, adds, and removes processes."""
        # Create scenario with: RobotCreate -> RobotMove
        scenario = ScenarioProxy()
        protocol = scenario.get_protocol()
        create = protocol.add_process(RobotCreate, "create")
        move = protocol.add_process(RobotMove, "move")
        protocol.add_connector(create >> "robot", move << "robot")
        scenario.run()

        scenario_model = scenario.refresh().get_model()
        self.assertEqual(scenario_model.status, ScenarioStatus.SUCCESS)
        self.assertEqual(len(scenario_model.protocol_model.processes), 2)

        # Create a new scenario with an extra process: RobotCreate -> RobotMove -> move_extra
        new_scenario = ScenarioProxy()
        new_protocol = new_scenario.get_protocol()
        new_create = new_protocol.add_process(RobotCreate, "create")
        new_move = new_protocol.add_process(RobotMove, "move")
        new_move_2 = new_protocol.add_process(RobotMove, "move_extra")
        new_protocol.add_connector(new_create >> "robot", new_move << "robot")
        new_protocol.add_connector(new_move >> "robot", new_move_2 << "robot")

        # Export with NEW_ID to avoid ID collisions on insert
        zip_info = ScenarioService.export_scenario(new_scenario.get_model().id)
        loader = ScenarioLoader(zip_info)
        loader.load_scenario()

        updater = ScenarioUpdater(scenario_model, loader)
        updated = updater.update_scenario(skip_tags=True)

        updated_protocol = updated.protocol_model
        # Should now have 3 processes (create, move, move_extra)
        self.assertEqual(len(updated_protocol.processes), 3)
        self.assertIsNotNone(updated_protocol.get_process("create"))
        self.assertIsNotNone(updated_protocol.get_process("move"))
        self.assertIsNotNone(updated_protocol.get_process("move_extra"))

    def test_update_scenario_removes_processes(self):
        """Test that processes present in old but not in new are removed."""
        resource_count_before = ResourceModel.select().count()

        # Create scenario with: RobotCreate -> RobotMove
        scenario = ScenarioProxy()
        protocol = scenario.get_protocol()
        create = protocol.add_process(RobotCreate, "create")
        move = protocol.add_process(RobotMove, "move")
        protocol.add_connector(create >> "robot", move << "robot")
        scenario.run()

        # Create a new scenario that uses the output resource
        # This is to test next scenario are cleaned up
        robot_output = move.refresh().get_output("robot")
        self.assertIsNotNone(robot_output)
        scenario2 = ScenarioProxy()
        protocol2 = scenario2.get_protocol()
        move = protocol2.add_process(RobotMove, "move")
        protocol2.add_source("robot_source", robot_output.get_model_id(), move << "robot")
        scenario2.run()

        scenario_model = scenario.refresh().get_model()
        self.assertEqual(len(scenario_model.protocol_model.processes), 2)
        self.assertEqual(ResourceModel.select().count(), resource_count_before + 3)

        # Create a new scenario with only RobotCreate (no RobotMove)
        new_scenario = ScenarioProxy()
        new_protocol = new_scenario.get_protocol()
        new_protocol.add_process(RobotCreate, "create")

        zip_info = ScenarioService.export_scenario(new_scenario.get_model().id)
        loader = ScenarioLoader(zip_info)
        loader.load_scenario()

        updater = ScenarioUpdater(scenario_model, loader)
        updated = updater.update_scenario(skip_tags=True)

        updated_protocol = updated.protocol_model
        self.assertEqual(len(updated_protocol.processes), 1)

        create_process = updated_protocol.get_process("create")
        self.assertEqual(create_process.id, create.get_model_id())

        # The removed process's generated resources should have been cleaned up
        self.assertEqual(ResourceModel.select().count(), resource_count_before + 1)

    def test_update_scenario_tags(self):
        """Test that tags are replaced during update."""
        scenario = ScenarioProxy()
        scenario.add_tag(_make_tag("key1", "value1"))

        # Create a new scenario with different tags
        new_scenario = ScenarioProxy()
        new_scenario.add_tag(_make_tag("key2", "value2", propagable=True))

        zip_info = ScenarioService.export_scenario(new_scenario.get_model().id)
        loader = ScenarioLoader(zip_info)
        loader.load_scenario()

        updater = ScenarioUpdater(scenario.get_model(), loader)
        updater.update_scenario(skip_tags=False)

        # Check that old tags were replaced by new tags
        updated_tags = EntityTagList.find_by_entity(TagEntityType.SCENARIO, scenario.get_model().id)
        tag_list = updated_tags.get_tags()
        self.assertEqual(len(tag_list), 1)
        self.assertEqual(tag_list[0].tag_key, "key2")
        self.assertEqual(tag_list[0].tag_value, "value2")

    def test_update_scenario_skip_tags(self):
        """Test that tags are preserved when skip_tags=True."""
        scenario = ScenarioProxy()
        scenario.add_tag(_make_tag("original_key", "original_value"))

        # Create a new scenario with different tags
        new_scenario = ScenarioProxy()
        new_scenario.add_tag(_make_tag("new_key", "new_value"))

        zip_info = ScenarioService.export_scenario(new_scenario.get_model().id)
        loader = ScenarioLoader(zip_info)
        loader.load_scenario()

        updater = ScenarioUpdater(scenario.get_model(), loader)
        updater.update_scenario(skip_tags=True)

        # Tags should remain unchanged
        updated_tags = EntityTagList.find_by_entity(TagEntityType.SCENARIO, scenario.get_model().id)
        tag_list = updated_tags.get_tags()
        self.assertEqual(len(tag_list), 1)
        self.assertEqual(tag_list[0].tag_key, "original_key")
        self.assertEqual(tag_list[0].tag_value, "original_value")

    def test_update_scenario_with_origin_lab_id(self):
        """Test that origin_lab_id is propagated to tags."""
        scenario = ScenarioProxy()

        new_scenario = ScenarioProxy()
        new_scenario.add_tag(_make_tag("shared_key", "shared_value", propagable=True))

        zip_info = ScenarioService.export_scenario(new_scenario.get_model().id)
        loader = ScenarioLoader(zip_info)
        loader.load_scenario()

        origin_lab_id = "external-lab-123"
        updater = ScenarioUpdater(scenario.get_model(), loader, origin_lab_id=origin_lab_id)
        updater.update_scenario(skip_tags=False)

        # Check that the tag has external lab origin set
        updated_tags = EntityTagList.find_by_entity(TagEntityType.SCENARIO, scenario.get_model().id)
        tag_list = updated_tags.get_tags()
        self.assertEqual(len(tag_list), 1)
        origins = tag_list[0].get_origins()
        origin_list = origins.get_origins()
        self.assertTrue(len(origin_list) > 0)
        self.assertEqual(origin_list[0].external_lab_origin_id, origin_lab_id)

    def test_update_scenario_config_and_resources(self):
        """Test that updating a scenario applies new config values and regenerates output resources."""
        # Create first scenario: RobotCreate -> RobotMove (default config)
        scenario_1 = ScenarioProxy()
        protocol_1 = scenario_1.get_protocol()
        create_1 = protocol_1.add_process(RobotCreate, "create")
        move_1 = protocol_1.add_process(RobotMove, "move")
        protocol_1.add_connector(create_1 >> "robot", move_1 << "robot")
        scenario_1.run()

        scenario_1.refresh()
        protocol_1.refresh()
        self.assertEqual(scenario_1.get_model().status, ScenarioStatus.SUCCESS)

        # Capture the output resource id of move in scenario 1
        move_1_output_id = protocol_1.get_process("move").get_output_resource_model("robot").id
        resource_count_after_second_run = ResourceModel.select().count()

        # Create second scenario: RobotCreate -> RobotMove with different config
        scenario_2 = ScenarioProxy()
        protocol_2 = scenario_2.get_protocol()
        create_2 = protocol_2.add_process(RobotCreate, "create")
        move_2 = protocol_2.add_process(RobotMove, "move")
        move_2.set_param("moving_step", 5.0)
        move_2.set_param("direction", "south")
        protocol_2.add_connector(create_2 >> "robot", move_2 << "robot")
        scenario_2.run()

        scenario_2.refresh()
        protocol_2.refresh()
        self.assertEqual(scenario_2.get_model().status, ScenarioStatus.SUCCESS)

        # Capture the output resource id of move in scenario 2
        move_2_output_id = protocol_2.get_process("move").get_output_resource_model("robot").id

        # Export scenario 2 and load it for updating scenario 1
        zip_info = ScenarioService.export_scenario(scenario_2.get_model().id)
        loader = ScenarioLoader(zip_info)
        loader.load_scenario()

        updater = ScenarioUpdater(scenario_1.get_model(), loader)
        updated = updater.update_scenario(skip_tags=True)

        # Verify the move process has the updated config
        updated_move = updated.protocol_model.get_process("move")
        self.assertEqual(updated_move.config.get_value("moving_step"), 5.0)
        self.assertEqual(updated_move.config.get_value("direction"), "south")

        # Verify the number of resources has not changed compared to after first run
        self.assertEqual(ResourceModel.select().count(), resource_count_after_second_run)

        # Verify the output resource id of move has changed (new resource generated)
        updated_move_output_id = updated_move.outputs.get_resource_model("robot").id
        self.assertNotEqual(updated_move_output_id, move_1_output_id)

        # Verify the output resource id is the same as scenario 2's output resource id
        self.assertEqual(updated_move_output_id, move_2_output_id)

        # Verify that move output id was deleted
        self.assertFalse(
            ResourceModel.select().where(ResourceModel.id == move_1_output_id).exists()
        )

    def test_get_existing_scenario(self):
        """Test that get_existing_scenario returns the correct scenario."""
        scenario = ScenarioProxy()
        new_scenario = ScenarioProxy()

        zip_info = ScenarioService.export_scenario(new_scenario.get_model().id)
        loader = ScenarioLoader(zip_info)
        loader.load_scenario()

        updater = ScenarioUpdater(scenario.get_model(), loader)
        self.assertEqual(updater.get_existing_scenario().id, scenario.get_model().id)
