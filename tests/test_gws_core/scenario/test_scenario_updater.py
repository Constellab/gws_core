from gws_core.external_lab.external_lab_api_service import ExternalLabApiService
from gws_core.folder.space_folder import SpaceFolder
from gws_core.impl.robot.robot_tasks import RobotCreate, RobotMove
from gws_core.protocol.protocol_dto import ProtocolGraphConfigDTO, ScenarioProtocolDTO
from gws_core.resource.resource_zipper import ResourceZipper
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_builder import ScenarioBuilder
from gws_core.scenario.scenario_enums import ScenarioStatus
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.scenario.scenario_service import ScenarioService
from gws_core.scenario.scenario_zipper import ScenarioExportPackage
from gws_core.share.shared_dto import ShareEntityCreateMode
from gws_core.tag.entity_tag_list import EntityTagList
from gws_core.tag.tag import Tag, TagOrigins
from gws_core.tag.tag_dto import TagOriginType
from gws_core.tag.tag_entity_type import TagEntityType
from gws_core.test.base_test_case import BaseTestCase
from gws_core.user.current_user_service import CurrentUserService


def _make_tag(key: str, value: str, propagable: bool = False) -> Tag:
    """Helper to create a Tag with a USER origin."""
    return Tag(key, value, is_propagable=propagable, origins=TagOrigins(TagOriginType.USER, "test"))


def _export_and_build_keep_id(
    scenario_package: ScenarioExportPackage,
    resource_zip_paths: dict[str, str],
    skip_scenario_tags: bool = True,
) -> Scenario:
    """Export a scenario, zip its resources, delete it, then rebuild with ScenarioBuilder in KEEP_ID mode.

    Returns the rebuilt scenario.
    """
    current_user = CurrentUserService.get_and_check_current_user()

    origin = ExternalLabApiService.get_current_lab_info(current_user)

    builder = ScenarioBuilder(
        scenario_info=scenario_package,
        resource_zip_paths=resource_zip_paths,
        origin=origin,
        create_mode=ShareEntityCreateMode.KEEP_ID,
        skip_scenario_tags=skip_scenario_tags,
    )
    try:
        return builder.build()
    finally:
        builder.cleanup()


# test_scenario_updater
class TestScenarioUpdater(BaseTestCase):
    # def test_update_scenario_metadata(self):
    #     """Test that scenario metadata (title, description, status, folder) is updated
    #     when rebuilding with ScenarioBuilder in KEEP_ID mode."""
    #     # Create an initial scenario with a specific folder
    #     folder = SpaceFolder(title="Updated folder")
    #     folder.save()
    #     scenario = ScenarioProxy(title="Updated title", folder=folder)
    #     scenario_model = scenario.get_model()
    #     original_id = scenario_model.id

    #     rebuilt = _export_and_build_keep_id(scenario_model)

    #     self.assertEqual(rebuilt.id, original_id)
    #     self.assertEqual(rebuilt.title, "Updated title")
    #     self.assertEqual(rebuilt.folder.id, folder.id)

    def test_update_scenario_with_processes(self):
        """Test that the protocol processes are correctly rebuilt with ScenarioBuilder in KEEP_ID mode."""
        # Create scenario with: RobotCreate -> RobotMove -> move_extra
        scenario = ScenarioProxy()
        protocol = scenario.get_protocol()
        create = protocol.add_process(RobotCreate, "create")
        move = protocol.add_process(RobotMove, "move")
        protocol.add_connector(create >> "robot", move << "robot")
        scenario.run()

        # Create a ScenarioExportPackage with only the Create process
        # Create manually
        graph = ProtocolGraphConfigDTO(
            nodes={}, links=[], interfaces={}, outerfaces={}, layout=None
        )
        graph.nodes["create"] = create.get_model().to_config_dto()
        main_protocol_dto = protocol.get_model().to_config_dto()
        main_protocol_dto.graph = graph

        scenario_package = ScenarioExportPackage(
            scenario=scenario.get_model().to_scenario_export_dto(),
            protocol=ScenarioProtocolDTO(data=main_protocol_dto),
            main_resource_models=[],
        )

        # Or create from a scenario and modify ids
        # scenario2 = ScenarioProxy()
        # protocol2 = scenario2.get_protocol()
        # create2 = protocol2.add_process(RobotCreate, "create")
        # scenario_package = ScenarioService.export_scenario(scenario2.get_model_id())
        # scenario_package.scenario.id = scenario.get_model_id()
        # scenario_package.protocol.data.id = protocol.get_model_id()
        # scenario_package.protocol.data.graph.nodes["create"].id = create.get_model_id()

        updated_scenario = _export_and_build_keep_id(scenario_package, resource_zip_paths={})

        # Verify that the updated scenario has the same protocol id and only the Create process
        protocol.refresh()
        create.refresh()
        self.assertEqual(scenario.get_model_id(), updated_scenario.id)
        self.assertEqual(protocol.get_model_id(), updated_scenario.protocol_model.id)
        self.assertEqual(create.get_model_id(), protocol.get_process("create").get_model_id())
        self.assertFalse(protocol.has_process("move"))

    # def test_update_scenario_config_and_resources(self):
    #     """Test that rebuilding a scenario with different config values produces correct resources."""
    #     # Create scenario: RobotCreate -> RobotMove with specific config
    #     scenario = ScenarioProxy()
    #     protocol = scenario.get_protocol()
    #     create = protocol.add_process(RobotCreate, "create")
    #     move = protocol.add_process(RobotMove, "move")
    #     move.set_param("moving_step", 5.0)
    #     move.set_param("direction", "south")
    #     protocol.add_connector(create >> "robot", move << "robot")
    #     scenario.run()

    #     scenario.refresh()
    #     protocol.refresh()
    #     self.assertEqual(scenario.get_model().status, ScenarioStatus.SUCCESS)

    #     scenario_model = scenario.get_model()

    #     rebuilt = _export_and_build_keep_id(scenario_model)

    #     # Verify the move process has the correct config
    #     rebuilt_move = rebuilt.protocol_model.get_process("move")
    #     self.assertEqual(rebuilt_move.config.get_value("moving_step"), 5.0)
    #     self.assertEqual(rebuilt_move.config.get_value("direction"), "south")
