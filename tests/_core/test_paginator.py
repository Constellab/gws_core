
# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from gws_core import (BaseTestCase, Experiment, ExperimentService, Paginator,
                      PaginatorDict, ProtocolModel, RobotService)


# test_paginator
class TestPaginator(BaseTestCase):

    def test_paginator(self):

        protocol: ProtocolModel = RobotService.create_robot_world_travel()
        ExperimentService.create_experiment_from_protocol_model(
            protocol_model=protocol, title="My title")

        query = Experiment.select().order_by(Experiment.created_at.desc())

        paginator: Paginator[Experiment] = Paginator(
            query, page=0, nb_of_items_per_page=20)

        # Test the paginator values
        paginator_dict: PaginatorDict = paginator.to_json()
        self.assertEqual(paginator_dict["page"], 0)
        self.assertEqual(paginator_dict["prev_page"], 0)
        self.assertEqual(paginator_dict["next_page"], 0)
        self.assertEqual(paginator_dict["last_page"], 0)
        self.assertEqual(paginator_dict["total_number_of_items"], 1)
        self.assertEqual(paginator_dict["total_number_of_pages"], 1)
        self.assertEqual(paginator_dict["number_of_items_per_page"], 20)
        self.assertEqual(paginator_dict["is_first_page"], True)
        self.assertEqual(paginator_dict["is_last_page"], True)

        # Test the experiment values
        self.assertEqual(paginator_dict["objects"][0]["title"], 'My title')
