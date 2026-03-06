from gws_core.entity_navigator.entity_navigator import (
    EntityNavigatorNote,
    EntityNavigatorResource,
    EntityNavigatorScenario,
    EntityNavigatorView,
)
from gws_core.entity_navigator.entity_navigator_service import EntityNavigatorService
from gws_core.entity_navigator.entity_navigator_type import NavigableEntityType
from gws_core.impl.robot.robot_tasks import RobotCreate, RobotMove
from gws_core.note.note import Note
from gws_core.note.note_dto import NoteSaveDTO
from gws_core.note.note_service import NoteService
from gws_core.protocol.protocol_proxy import ProtocolProxy
from gws_core.resource.resource_model import ResourceModel
from gws_core.resource.resource_service import ResourceService
from gws_core.resource.view_config.view_config import ViewConfig
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_proxy import ScenarioProxy
from gws_core.test.base_test_case import BaseTestCase


# test_entity_navigator.py
class TestEntityNavigator(BaseTestCase):
    scenario_1: Scenario
    scenario_2: Scenario
    scenario_3: Scenario
    scenario_4: Scenario

    scenario_1_resource_1: ResourceModel
    scenario_1_resource_2: ResourceModel
    scenario_2_resource_1: ResourceModel
    scenario_2_resource_2: ResourceModel
    scenario_3_resource_1: ResourceModel
    scenario_4_resource_1: ResourceModel

    scenario_1_resource_1_view_1: ViewConfig

    # note associated to scenario_1
    # note uses view scenario_1_resource_1_view_1
    note_1: Note

    def test_entity_navigator(self):
        self._create_scenarios()
        self._create_views()
        self._create_note()

        self._test_scenario_navigation()
        self._test_resource_navigation()
        self._test_view_navigation()
        self._test_note_navigation()
        self._test_recursive_navigation()
        self._test_entity_nav_service()

    def _create_scenarios(self):
        # Scenario dependency tree:
        #   scenario_1 (RobotCreate -> RobotMove)
        #   ├── res_1 (output of RobotCreate)
        #   ├── res_2 (output of RobotMove, uses res_1)
        #   ├── scenario_2 (uses scenario_1.res_1 and scenario_1.res_2)
        #   │   ├── res_1 (output of RobotMove, uses scenario_1.res_1)
        #   │   ├── res_2 (output of RobotMove, uses scenario_1.res_2)
        #   │   └── scenario_3 (uses scenario_2.res_2)
        #   │       └── res_1 (output of RobotMove)
        #   └── scenario_4 (uses scenario_1.res_1 and scenario_2.res_1)
        #       └── res_1 (output of RobotMove)

        # first scenario RobotCreate -> RobotMove
        scenario_1 = ScenarioProxy(title="Scenario 1")
        i_protocol_1: ProtocolProxy = scenario_1.get_protocol()
        create_robot = i_protocol_1.add_task(RobotCreate, "create_robot")
        move_robot_1 = i_protocol_1.add_task(RobotMove, "move_robot")
        i_protocol_1.add_connector(create_robot >> "robot", move_robot_1 << "robot")
        scenario_1.run()

        create_robot.refresh()
        move_robot_1.refresh()

        robot_1 = create_robot.get_output_resource_model("robot")
        robot_2 = move_robot_1.get_output_resource_model("robot")

        # second scenario Input -> RobotMove
        scenario_2 = ScenarioProxy(title="Scenario 2")
        i_protocol_2: ProtocolProxy = scenario_2.get_protocol()
        move_robot_2 = i_protocol_2.add_task(RobotMove, "move_robot")
        move_robot_3 = i_protocol_2.add_task(RobotMove, "move_robot_1")
        i_protocol_2.add_resource("source_1", robot_1.id, move_robot_2 << "robot")
        i_protocol_2.add_resource("source_2", robot_2.id, move_robot_3 << "robot")
        scenario_2.run()

        move_robot_2.refresh()
        move_robot_3.refresh()

        # Retrieve the models
        self.scenario_1 = scenario_1.get_model()
        self.scenario_2 = scenario_2.get_model()

        self.scenario_1_resource_1 = create_robot.get_output_resource_model("robot")
        self.scenario_1_resource_2 = move_robot_1.get_output_resource_model("robot")
        self.scenario_2_resource_1 = move_robot_2.get_output_resource_model("robot")
        self.scenario_2_resource_2 = move_robot_3.get_output_resource_model("robot")

        # third scenario scenario_2_resource_2 -> RobotMove
        scenario_3 = ScenarioProxy(title="Scenario 3")
        i_protocol_3: ProtocolProxy = scenario_3.get_protocol()
        move_robot_4 = i_protocol_3.add_task(RobotMove, "move_robot")
        i_protocol_3.add_resource(
            "source_1", self.scenario_2_resource_2.id, move_robot_4 << "robot"
        )
        scenario_3.run()

        move_robot_4.refresh()

        self.scenario_3 = scenario_3.get_model()
        self.scenario_3_resource_1 = move_robot_4.get_output_resource_model("robot")

        # fourth scenario uses resources from both scenario_1 and scenario_2
        # This tests the edge case where a scenario is reachable at multiple depths.
        # Deleting scenario_1 should correctly cascade-delete scenario_4 without FK errors,
        # because source_config_id references are cleared before deletion.
        scenario_4 = ScenarioProxy(title="Scenario 4")
        i_protocol_4: ProtocolProxy = scenario_4.get_protocol()
        move_robot_5 = i_protocol_4.add_task(RobotMove, "move_robot")
        move_robot_6 = i_protocol_4.add_task(RobotMove, "move_robot_1")
        i_protocol_4.add_resource(
            "source_1", self.scenario_1_resource_1.id, move_robot_5 << "robot"
        )
        i_protocol_4.add_resource(
            "source_2", self.scenario_2_resource_1.id, move_robot_6 << "robot"
        )
        scenario_4.run()

        move_robot_5.refresh()

        self.scenario_4 = scenario_4.get_model()
        self.scenario_4_resource_1 = move_robot_5.get_output_resource_model("robot")

    def _create_views(self):
        view_result = ResourceService.call_view_on_resource_model(
            self.scenario_1_resource_1, "view_as_json", {}, True
        )
        self.scenario_1_resource_1_view_1 = view_result.view_config

    def _create_note(self):
        note_1 = NoteService.create(NoteSaveDTO(title="test_note"))

        NoteService.add_scenario(note_1.id, self.scenario_1.id)
        NoteService.add_view_to_content(note_1.id, self.scenario_1_resource_1_view_1.id)

        self.note_1 = note_1.refresh()

    def _test_scenario_navigation(self):
        # Test get next scenario of scenario 1
        scenario_nav = EntityNavigatorScenario(self.scenario_1)
        next_scenarios = scenario_nav.get_next_scenarios().get_entities_list()
        self.assertEqual(len(next_scenarios), 2)
        next_scenario_ids = {scenario.id for scenario in next_scenarios}
        self.assertIn(self.scenario_2.id, next_scenario_ids)
        self.assertIn(self.scenario_4.id, next_scenario_ids)

        # Test get next resources of scenario 1
        next_resources = scenario_nav.get_next_resources().get_entities_list()
        self.assertEqual(len(next_resources), 2)
        self.assertIsNotNone(
            len([x for x in next_resources if x.id == self.scenario_1_resource_1.id])
        )
        self.assertIsNotNone(
            len([x for x in next_resources if x.id == self.scenario_1_resource_2.id])
        )

        # Test get next scenario of scenario 3
        scenario_nav = EntityNavigatorScenario(self.scenario_3)
        next_scenarios = scenario_nav.get_next_scenarios().get_entities_list()
        self.assertEqual(len(next_scenarios), 0)

        # Test get next resources of scenario 2
        scenario_nav = EntityNavigatorScenario(self.scenario_2)
        next_resources = scenario_nav.get_next_resources().get_entities_list()
        self.assertEqual(len(next_resources), 2)
        self.assertIsNotNone(
            len([x for x in next_resources if x.id == self.scenario_2_resource_1.id])
        )
        self.assertIsNotNone(
            len([x for x in next_resources if x.id == self.scenario_2_resource_2.id])
        )

        # Test get previous scenario of scenario 2
        scenario_nav = EntityNavigatorScenario(self.scenario_2)
        prev_scenarios = scenario_nav.get_previous_scenarios().get_entities_list()
        self.assertEqual(len(prev_scenarios), 1)
        self.assertEqual(prev_scenarios[0].id, self.scenario_1.id)

        # Test get previous resources of scenario 2
        scenario_nav = EntityNavigatorScenario(self.scenario_2)
        prev_resources = scenario_nav.get_previous_resources().get_entities_list()
        self.assertEqual(len(prev_resources), 2)
        self.assertIsNotNone(
            len([x for x in prev_resources if x.id == self.scenario_1_resource_1.id])
        )
        self.assertIsNotNone(
            len([x for x in prev_resources if x.id == self.scenario_1_resource_2.id])
        )

        # Test get previous scenario of scenario 1
        scenario_nav = EntityNavigatorScenario(self.scenario_1)
        prev_scenarios = scenario_nav.get_previous_scenarios().get_entities_list()
        self.assertEqual(len(prev_scenarios), 0)

        # Test get previous resources of scenario 1
        scenario_nav = EntityNavigatorScenario(self.scenario_1)
        prev_resources = scenario_nav.get_previous_resources().get_entities_list()
        self.assertEqual(len(prev_resources), 0)

        # Test get next note of scenario 1
        scenario_nav = EntityNavigatorScenario(self.scenario_1)
        next_notes = scenario_nav.get_next_notes().get_entities_list()
        self.assertEqual(len(next_notes), 1)
        self.assertEqual(next_notes[0].id, self.note_1.id)

        # Test get next note of scenario 2
        scenario_nav = EntityNavigatorScenario(self.scenario_2)
        next_notes = scenario_nav.get_next_notes().get_entities_list()
        self.assertEqual(len(next_notes), 0)

        # Test get next view of scenario 1
        scenario_nav = EntityNavigatorScenario(self.scenario_1)
        next_views = scenario_nav.get_next_views().get_entities_list()
        self.assertEqual(len(next_views), 1)
        self.assertEqual(next_views[0].id, self.scenario_1_resource_1_view_1.id)

        # Test get next view of scenario 2
        scenario_nav = EntityNavigatorScenario(self.scenario_2)
        next_views = scenario_nav.get_next_views().get_entities_list()
        self.assertEqual(len(next_views), 0)

    def _test_resource_navigation(self):
        # Test get next resource of resource 1 scenario 1
        resource_nav = EntityNavigatorResource(self.scenario_1_resource_1)
        next_resources = resource_nav.get_next_resources().get_entities_list()
        self.assertEqual(len(next_resources), 3)
        # Resource 2 of scenario 1
        self.assertIsNotNone(
            len([x for x in next_resources if x.id == self.scenario_1_resource_2.id])
        )
        # Resource 1 of scenario 2
        self.assertIsNotNone(
            len([x for x in next_resources if x.id == self.scenario_2_resource_1.id])
        )
        # Resource 1 of scenario 4
        self.assertIsNotNone(
            len([x for x in next_resources if x.id == self.scenario_4_resource_1.id])
        )

        # Test get next resource of resource 2 scenario 1
        resource_nav = EntityNavigatorResource(self.scenario_1_resource_2)
        next_resources = resource_nav.get_next_resources().get_entities_list()
        self.assertEqual(len(next_resources), 1)
        # Resource 2 of scenario 2
        self.assertIsNotNone(
            len([x for x in next_resources if x.id == self.scenario_2_resource_2.id])
        )

        # Test previous resources of resource 1 scenario 2
        resource_nav = EntityNavigatorResource(self.scenario_2_resource_1)
        prev_resources = resource_nav.get_previous_resources().get_entities_list()
        self.assertEqual(len(prev_resources), 1)
        # Resource 1 of scenario 1
        self.assertIsNotNone(
            len([x for x in prev_resources if x.id == self.scenario_1_resource_1.id])
        )

        # Test previous resources of resource 2 scenario 1
        resource_nav = EntityNavigatorResource(self.scenario_1_resource_2)
        prev_resources = resource_nav.get_previous_resources().get_entities_list()
        self.assertEqual(len(prev_resources), 1)
        # Resource 1 of scenario 1
        self.assertIsNotNone(
            len([x for x in prev_resources if x.id == self.scenario_1_resource_1.id])
        )

        # Test next views of resource 1 scenario 1
        resource_nav = EntityNavigatorResource(self.scenario_1_resource_1)
        next_views = resource_nav.get_next_views().get_entities_list()
        self.assertEqual(len(next_views), 1)
        # View 1 of resource 1 scenario 1
        self.assertIsNotNone(
            len([x for x in next_views if x.id == self.scenario_1_resource_1_view_1.id])
        )

        # Test next views of resource 2 scenario 1
        resource_nav = EntityNavigatorResource(self.scenario_1_resource_2)
        next_views = resource_nav.get_next_views().get_entities_list()
        self.assertEqual(len(next_views), 0)

        # Test next note of resource 1 scenario 1
        resource_nav = EntityNavigatorResource(self.scenario_1_resource_1)
        next_notes = resource_nav.get_next_notes().get_entities_list()
        self.assertEqual(len(next_notes), 1)
        # Note 1
        self.assertIsNotNone(len([x for x in next_notes if x.id == self.note_1.id]))

        # Test next note of resource 2 scenario 1
        resource_nav = EntityNavigatorResource(self.scenario_1_resource_2)
        next_notes = resource_nav.get_next_notes().get_entities_list()
        self.assertEqual(len(next_notes), 0)

    def _test_view_navigation(self):
        view_nav = EntityNavigatorView(self.scenario_1_resource_1_view_1)

        # Test next note of view 1
        next_notes = view_nav.get_next_notes().get_entities_list()
        self.assertEqual(len(next_notes), 1)
        self.assertIsNotNone(len([x for x in next_notes if x.id == self.note_1.id]))

        # Test get previous resources of view 1
        prev_resources = view_nav.get_previous_resources().get_entities_list()
        self.assertEqual(len(prev_resources), 1)
        self.assertIsNotNone(
            len([x for x in prev_resources if x.id == self.scenario_1_resource_1.id])
        )

        # Test get previous scenario of view 1
        prev_scenarios = view_nav.get_previous_scenarios().get_entities_list()
        self.assertEqual(len(prev_scenarios), 1)
        self.assertIsNotNone(len([x for x in prev_scenarios if x.id == self.scenario_1.id]))

    def _test_note_navigation(self):
        note_nav = EntityNavigatorNote(self.note_1)

        # Test get previous scenario of note 1
        prev_scenarios = note_nav.get_previous_scenarios().get_entities_list()
        self.assertEqual(len(prev_scenarios), 1)
        self.assertIsNotNone(len([x for x in prev_scenarios if x.id == self.scenario_1.id]))

        # Test get previous view of note 1
        prev_views = note_nav.get_previous_views().get_entities_list()
        self.assertEqual(len(prev_views), 1)
        self.assertIsNotNone(
            len([x for x in prev_views if x.id == self.scenario_1_resource_1_view_1.id])
        )

        # Test get previous resource of note 1
        prev_resources = note_nav.get_previous_resources().get_entities_list()
        self.assertEqual(len(prev_resources), 1)
        self.assertIsNotNone(
            len([x for x in prev_resources if x.id == self.scenario_1_resource_1.id])
        )

    def _test_recursive_navigation(self):
        scenario = EntityNavigatorScenario(self.scenario_1)

        # Test get next entities of scenario 1
        next_scenarios = scenario.get_next_entities_recursive()

        # test the get deepest level
        scenarios = next_scenarios.get_entities_from_deepest_level(NavigableEntityType.SCENARIO)
        self.assertEqual(len(scenarios), 3)

        # Verify deep_levels
        scenario_deeps = next_scenarios.get_entity_deep_by_type(NavigableEntityType.SCENARIO)
        scenario_2_depth = None
        scenario_3_depth = None
        scenario_4_depth = None
        for sd in scenario_deeps:
            if sd.entity.id == self.scenario_2.id:
                scenario_2_depth = sd.deep_level
            elif sd.entity.id == self.scenario_3.id:
                scenario_3_depth = sd.deep_level
            elif sd.entity.id == self.scenario_4.id:
                scenario_4_depth = sd.deep_level

        # scenario_3 and scenario_4 both depend on scenario_2's outputs, so they should be at the same depth
        # and deeper than scenario_2
        self.assertEqual(scenario_2_depth, 2)
        self.assertEqual(scenario_3_depth, 3)
        self.assertEqual(scenario_4_depth, 3)

        # get_entities_from_deepest_level should return scenario_3 and scenario_4 first (deepest), then scenario_2
        deepest_scenario_ids = {scenarios[0].id, scenarios[1].id}
        self.assertIn(self.scenario_3.id, deepest_scenario_ids)
        self.assertIn(self.scenario_4.id, deepest_scenario_ids)
        self.assertEqual(scenarios[2].id, self.scenario_2.id)

        # Test get next entities of scenario 2
        scenario = EntityNavigatorScenario(self.scenario_2)
        next_scenarios = scenario.get_next_entities_recursive()

        # Test previous entities of scenario 3
        scenario = EntityNavigatorScenario(self.scenario_3)
        prev_scenarios = list(scenario.get_previous_entities_recursive())
        self.assertEqual(len(prev_scenarios), 5)

        # Test previous entities of scenario 2
        scenario = EntityNavigatorScenario(self.scenario_2)
        prev_scenarios = list(scenario.get_previous_entities_recursive())
        self.assertEqual(len(prev_scenarios), 3)

    def _test_entity_nav_service(self):
        result = EntityNavigatorService.check_impact_for_scenario_reset(self.scenario_1.id)
        self.assertTrue(result.has_entities())
        self.assertEqual(
            len(result.impacted_entities.get_entity_by_type(NavigableEntityType.SCENARIO)), 3
        )
        self.assertEqual(
            len(result.impacted_entities.get_entity_by_type(NavigableEntityType.NOTE)), 1
        )

        result = EntityNavigatorService.check_impact_for_scenario_reset(self.scenario_2.id)
        self.assertTrue(result.has_entities())
        self.assertEqual(
            len(result.impacted_entities.get_entity_by_type(NavigableEntityType.SCENARIO)), 2
        )
        self.assertEqual(
            len(result.impacted_entities.get_entity_by_type(NavigableEntityType.NOTE)), 0
        )

        result = EntityNavigatorService.check_impact_for_scenario_reset(self.scenario_3.id)
        self.assertFalse(result.has_entities())

        result = EntityNavigatorService.check_impact_for_scenario_reset(self.scenario_4.id)
        self.assertFalse(result.has_entities())

        # delete the first scenario, this also tests that scenarios reachable at multiple depths
        # are deleted in the correct order (deepest first)
        EntityNavigatorService.delete_scenario(self.scenario_1.id)

        # check that everything is deleted
        self.assertIsNone(Scenario.get_by_id(self.scenario_1.id))
        self.assertIsNone(ResourceModel.get_by_id(self.scenario_1_resource_1.id))
        self.assertIsNone(ResourceModel.get_by_id(self.scenario_1_resource_2.id))
        self.assertIsNone(Note.get_by_id(self.note_1.id))
        self.assertIsNone(Scenario.get_by_id(self.scenario_2.id))
        self.assertIsNone(Scenario.get_by_id(self.scenario_3.id))
        self.assertIsNone(Scenario.get_by_id(self.scenario_4.id))
