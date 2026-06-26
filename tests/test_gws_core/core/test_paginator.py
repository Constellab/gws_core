from gws_core import BaseTestCase, Paginator, Scenario, ScenarioService
from gws_core.impl.robot.robot_protocol import RobotWorldTravelProto


# test_paginator
class TestPaginator(BaseTestCase):
    def test_paginator(self):
        ScenarioService.create_scenario_from_protocol_type(
            RobotWorldTravelProto, title="My title"
        )

        query = Scenario.select().order_by(Scenario.created_at.desc())

        paginator: Paginator[Scenario] = Paginator(query, page=0, nb_of_items_per_page=20)

        # Test the paginator values
        paginator_dto = paginator.to_dto()
        self.assertEqual(paginator_dto.page, 0)
        self.assertEqual(paginator_dto.prev_page, 0)
        self.assertEqual(paginator_dto.next_page, 0)
        self.assertEqual(paginator_dto.last_page, 0)
        self.assertEqual(paginator_dto.total_number_of_items, 1)
        self.assertEqual(paginator_dto.total_number_of_pages, 1)
        self.assertEqual(paginator_dto.number_of_items_per_page, 20)
        self.assertEqual(paginator_dto.is_first_page, True)
        self.assertEqual(paginator_dto.is_last_page, True)

        # Test the scenario values
        self.assertEqual(paginator_dto.objects[0].title, "My title")
