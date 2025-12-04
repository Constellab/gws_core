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
    exp_1: Scenario
    exp_2: Scenario
    exp_3: Scenario

    exp_1_resource_1: ResourceModel
    exp_1_resource_2: ResourceModel
    exp_2_resource_1: ResourceModel
    exp_2_resource_2: ResourceModel
    exp_3_resource_1: ResourceModel

    exp_1_resource_1_view_1: ViewConfig

    # note associated to exp_1
    # note uses view exp_1_resource_1_view_1
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
        # first scenario RobotCreate -> RobotMove
        scenario_1 = ScenarioProxy()
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
        scenario_2 = ScenarioProxy()
        i_protocol_2: ProtocolProxy = scenario_2.get_protocol()
        move_robot_2 = i_protocol_2.add_task(RobotMove, "move_robot")
        move_robot_3 = i_protocol_2.add_task(RobotMove, "move_robot_1")
        i_protocol_2.add_resource("source_1", robot_1.id, move_robot_2 << "robot")
        i_protocol_2.add_resource("source_2", robot_2.id, move_robot_3 << "robot")
        scenario_2.run()

        move_robot_2.refresh()
        move_robot_3.refresh()

        # Retrieve the models
        self.exp_1 = scenario_1.get_model()
        self.exp_2 = scenario_2.get_model()

        self.exp_1_resource_1 = create_robot.get_output_resource_model("robot")
        self.exp_1_resource_2 = move_robot_1.get_output_resource_model("robot")
        self.exp_2_resource_1 = move_robot_2.get_output_resource_model("robot")
        self.exp_2_resource_2 = move_robot_3.get_output_resource_model("robot")

        # third scenario exp_2_resource_2 -> RobotMove
        scenario_3 = ScenarioProxy()
        i_protocol_3: ProtocolProxy = scenario_3.get_protocol()
        move_robot_4 = i_protocol_3.add_task(RobotMove, "move_robot")
        i_protocol_3.add_resource("source_1", self.exp_2_resource_2.id, move_robot_4 << "robot")
        scenario_3.run()

        move_robot_4.refresh()

        self.exp_3 = scenario_3.get_model()
        self.exp_3_resource_1 = move_robot_4.get_output_resource_model("robot")

    def _create_views(self):
        view_result = ResourceService.call_view_on_resource_model(
            self.exp_1_resource_1, "view_as_json", {}, True
        )
        self.exp_1_resource_1_view_1 = view_result.view_config

    def _create_note(self):
        note_1 = NoteService.create(NoteSaveDTO(title="test_note"))

        NoteService.add_scenario(note_1.id, self.exp_1.id)
        NoteService.add_view_to_content(note_1.id, self.exp_1_resource_1_view_1.id)

        self.note_1 = note_1.refresh()

    def _test_scenario_navigation(self):
        # Test get next scenario of scenario 1
        exp_nav = EntityNavigatorScenario(self.exp_1)
        next_exps = exp_nav.get_next_scenarios().get_entities_list()
        self.assertEqual(len(next_exps), 1)
        self.assertEqual(next_exps[0].id, self.exp_2.id)

        # Test get next resources of scenario 1
        next_resources = exp_nav.get_next_resources().get_entities_list()
        self.assertEqual(len(next_resources), 2)
        self.assertIsNotNone(len([x for x in next_resources if x.id == self.exp_1_resource_1.id]))
        self.assertIsNotNone(len([x for x in next_resources if x.id == self.exp_1_resource_2.id]))

        # Test get next scenario of scenario 3
        exp_nav = EntityNavigatorScenario(self.exp_3)
        next_exps = exp_nav.get_next_scenarios().get_entities_list()
        self.assertEqual(len(next_exps), 0)

        # Test get next resources of scenario 2
        exp_nav = EntityNavigatorScenario(self.exp_2)
        next_resources = exp_nav.get_next_resources().get_entities_list()
        self.assertEqual(len(next_resources), 2)
        self.assertIsNotNone(len([x for x in next_resources if x.id == self.exp_2_resource_1.id]))
        self.assertIsNotNone(len([x for x in next_resources if x.id == self.exp_2_resource_2.id]))

        # Test get previous scenario of scenario 2
        exp_nav = EntityNavigatorScenario(self.exp_2)
        prev_exps = exp_nav.get_previous_scenarios().get_entities_list()
        self.assertEqual(len(prev_exps), 1)
        self.assertEqual(prev_exps[0].id, self.exp_1.id)

        # Test get previous resources of scenario 2
        exp_nav = EntityNavigatorScenario(self.exp_2)
        prev_resources = exp_nav.get_previous_resources().get_entities_list()
        self.assertEqual(len(prev_resources), 2)
        self.assertIsNotNone(len([x for x in prev_resources if x.id == self.exp_1_resource_1.id]))
        self.assertIsNotNone(len([x for x in prev_resources if x.id == self.exp_1_resource_2.id]))

        # Test get previous scenario of scenario 1
        exp_nav = EntityNavigatorScenario(self.exp_1)
        prev_exps = exp_nav.get_previous_scenarios().get_entities_list()
        self.assertEqual(len(prev_exps), 0)

        # Test get previous resources of scenario 1
        exp_nav = EntityNavigatorScenario(self.exp_1)
        prev_resources = exp_nav.get_previous_resources().get_entities_list()
        self.assertEqual(len(prev_resources), 0)

        # Test get next note of scenario 1
        exp_nav = EntityNavigatorScenario(self.exp_1)
        next_notes = exp_nav.get_next_notes().get_entities_list()
        self.assertEqual(len(next_notes), 1)
        self.assertEqual(next_notes[0].id, self.note_1.id)

        # Test get next note of scenario 2
        exp_nav = EntityNavigatorScenario(self.exp_2)
        next_notes = exp_nav.get_next_notes().get_entities_list()
        self.assertEqual(len(next_notes), 0)

        # Test get next view of scenario 1
        exp_nav = EntityNavigatorScenario(self.exp_1)
        next_views = exp_nav.get_next_views().get_entities_list()
        self.assertEqual(len(next_views), 1)
        self.assertEqual(next_views[0].id, self.exp_1_resource_1_view_1.id)

        # Test get next view of scenario 2
        exp_nav = EntityNavigatorScenario(self.exp_2)
        next_views = exp_nav.get_next_views().get_entities_list()
        self.assertEqual(len(next_views), 0)

    def _test_resource_navigation(self):
        # Test get next resource of resource 1 exp 1
        resource_nav = EntityNavigatorResource(self.exp_1_resource_1)
        next_resources = resource_nav.get_next_resources().get_entities_list()
        self.assertEqual(len(next_resources), 2)
        # Resource 2 of exp 1
        self.assertIsNotNone(len([x for x in next_resources if x.id == self.exp_1_resource_2.id]))
        # Resource 1 of exp 2
        self.assertIsNotNone(len([x for x in next_resources if x.id == self.exp_2_resource_1.id]))

        # Test get next resource of resource 2 exp 1
        resource_nav = EntityNavigatorResource(self.exp_1_resource_2)
        next_resources = resource_nav.get_next_resources().get_entities_list()
        self.assertEqual(len(next_resources), 1)
        # Resource 2 of exp 2
        self.assertIsNotNone(len([x for x in next_resources if x.id == self.exp_2_resource_2.id]))

        # Test previous resources of resource 1 exp 2
        resource_nav = EntityNavigatorResource(self.exp_2_resource_1)
        prev_resources = resource_nav.get_previous_resources().get_entities_list()
        self.assertEqual(len(prev_resources), 1)
        # Resource 1 of exp 1
        self.assertIsNotNone(len([x for x in prev_resources if x.id == self.exp_1_resource_1.id]))

        # Test previous resources of resource 2 exp 1
        resource_nav = EntityNavigatorResource(self.exp_1_resource_2)
        prev_resources = resource_nav.get_previous_resources().get_entities_list()
        self.assertEqual(len(prev_resources), 1)
        # Resource 1 of exp 1
        self.assertIsNotNone(len([x for x in prev_resources if x.id == self.exp_1_resource_1.id]))

        # Test next views of resource 1 exp 1
        resource_nav = EntityNavigatorResource(self.exp_1_resource_1)
        next_views = resource_nav.get_next_views().get_entities_list()
        self.assertEqual(len(next_views), 1)
        # View 1 of resource 1 exp 1
        self.assertIsNotNone(
            len([x for x in next_views if x.id == self.exp_1_resource_1_view_1.id])
        )

        # Test next views of resource 2 exp 1
        resource_nav = EntityNavigatorResource(self.exp_1_resource_2)
        next_views = resource_nav.get_next_views().get_entities_list()
        self.assertEqual(len(next_views), 0)

        # Test next note of resource 1 exp 1
        resource_nav = EntityNavigatorResource(self.exp_1_resource_1)
        next_notes = resource_nav.get_next_notes().get_entities_list()
        self.assertEqual(len(next_notes), 1)
        # Note 1
        self.assertIsNotNone(len([x for x in next_notes if x.id == self.note_1.id]))

        # Test next note of resource 2 exp 1
        resource_nav = EntityNavigatorResource(self.exp_1_resource_2)
        next_notes = resource_nav.get_next_notes().get_entities_list()
        self.assertEqual(len(next_notes), 0)

    def _test_view_navigation(self):
        view_nav = EntityNavigatorView(self.exp_1_resource_1_view_1)

        # Test next note of view 1
        next_notes = view_nav.get_next_notes().get_entities_list()
        self.assertEqual(len(next_notes), 1)
        self.assertIsNotNone(len([x for x in next_notes if x.id == self.note_1.id]))

        # Test get previous resources of view 1
        prev_resources = view_nav.get_previous_resources().get_entities_list()
        self.assertEqual(len(prev_resources), 1)
        self.assertIsNotNone(len([x for x in prev_resources if x.id == self.exp_1_resource_1.id]))

        # Test get previous scenario of view 1
        prev_exps = view_nav.get_previous_scenarios().get_entities_list()
        self.assertEqual(len(prev_exps), 1)
        self.assertIsNotNone(len([x for x in prev_exps if x.id == self.exp_1.id]))

    def _test_note_navigation(self):
        note_nav = EntityNavigatorNote(self.note_1)

        # Test get previous scenario of note 1
        prev_exps = note_nav.get_previous_scenarios().get_entities_list()
        self.assertEqual(len(prev_exps), 1)
        self.assertIsNotNone(len([x for x in prev_exps if x.id == self.exp_1.id]))

        # Test get previous view of note 1
        prev_views = note_nav.get_previous_views().get_entities_list()
        self.assertEqual(len(prev_views), 1)
        self.assertIsNotNone(
            len([x for x in prev_views if x.id == self.exp_1_resource_1_view_1.id])
        )

        # Test get previous resource of note 1
        prev_resources = note_nav.get_previous_resources().get_entities_list()
        self.assertEqual(len(prev_resources), 1)
        self.assertIsNotNone(len([x for x in prev_resources if x.id == self.exp_1_resource_1.id]))

    def _test_recursive_navigation(self):
        exp = EntityNavigatorScenario(self.exp_1)

        # Test get next entities of scenario 1
        next_exps = exp.get_next_entities_recursive()

        # return everything
        self.assertEqual(len(next_exps), 9)

        # test the get deepest level
        scenarios = next_exps.get_entities_from_deepest_level(NavigableEntityType.SCENARIO)
        self.assertEqual(len(scenarios), 2)
        self.assertEqual(scenarios[0].id, self.exp_3.id)
        self.assertEqual(scenarios[1].id, self.exp_2.id)

        # Test get next entities of scenario 2
        exp = EntityNavigatorScenario(self.exp_2)
        next_exps = exp.get_next_entities_recursive()
        self.assertEqual(len(next_exps), 4)

        # Test previous entities of scenario 3
        exp = EntityNavigatorScenario(self.exp_3)
        prev_exps = list(exp.get_previous_entities_recursive())
        self.assertEqual(len(prev_exps), 5)

        # Test previous entities of scenario 2
        exp = EntityNavigatorScenario(self.exp_2)
        prev_exps = list(exp.get_previous_entities_recursive())
        self.assertEqual(len(prev_exps), 3)

    def _test_entity_nav_service(self):
        result = EntityNavigatorService.check_impact_for_scenario_reset(self.exp_1.id)
        self.assertTrue(result.has_entities())
        self.assertEqual(
            len(result.impacted_entities.get_entity_by_type(NavigableEntityType.SCENARIO)), 2
        )
        self.assertEqual(
            len(result.impacted_entities.get_entity_by_type(NavigableEntityType.NOTE)), 1
        )

        result = EntityNavigatorService.check_impact_for_scenario_reset(self.exp_2.id)
        self.assertTrue(result.has_entities())
        self.assertEqual(
            len(result.impacted_entities.get_entity_by_type(NavigableEntityType.SCENARIO)), 1
        )
        self.assertEqual(
            len(result.impacted_entities.get_entity_by_type(NavigableEntityType.NOTE)), 0
        )

        result = EntityNavigatorService.check_impact_for_scenario_reset(self.exp_3.id)
        self.assertFalse(result.has_entities())

        # delete the first exp
        EntityNavigatorService.delete_scenario(self.exp_1.id)

        # check that everything is deleted
        self.assertIsNone(Scenario.get_by_id(self.exp_1.id))
        self.assertIsNone(ResourceModel.get_by_id(self.exp_1_resource_1.id))
        self.assertIsNone(ResourceModel.get_by_id(self.exp_1_resource_2.id))
        self.assertIsNone(Note.get_by_id(self.note_1.id))
        self.assertIsNone(Scenario.get_by_id(self.exp_2.id))
        self.assertIsNone(Scenario.get_by_id(self.exp_3.id))
