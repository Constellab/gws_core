

from gws_core.core.classes.search_builder import (SearchFilterCriteria,
                                                  SearchOperator, SearchParams)
from gws_core.folder.space_folder import SpaceFolder
from gws_core.scenario.scenario import Scenario
from gws_core.scenario.scenario_enums import ScenarioStatus
from gws_core.scenario.scenario_service import ScenarioService
from gws_core.test.base_test_case import BaseTestCase
from gws_core.test.gtest import GTest


# test_scenario_search
class TestScenarioSearch(BaseTestCase):

    def test_search(self):
        scenario_1 = ScenarioService.create_scenario(
            title="My first scenario title world")

        scenario_2: Scenario = ScenarioService.create_scenario(
            title="The second one world")
        scenario_2.mark_as_success()

        folder: SpaceFolder = GTest.create_default_folder()
        scenario_2.folder = folder
        scenario_2.is_validated = True
        scenario_2.save()

        search_dict: SearchParams = SearchParams()

        # Test title search
        search_dict.set_filters_criteria([SearchFilterCriteria(
            key="title", operator=SearchOperator.CONTAINS, value="enario")])
        self.search(search_dict, 1)

        # Test status search
        search_dict.set_filters_criteria([
            SearchFilterCriteria(
                key="status", operator=SearchOperator.EQ,
                value=ScenarioStatus.SUCCESS.value)])
        self.search(search_dict, 1)

        # Test validate search
        search_dict.set_filters_criteria([SearchFilterCriteria(
            key="is_validated", operator=SearchOperator.EQ, value=True)])
        self.search(search_dict, 1)

        # Test with folder
        search_dict.set_filters_criteria([SearchFilterCriteria(
            key="folder", operator=SearchOperator.IN, value=[folder.id])])
        self.search(search_dict, 1)

    def search(self, search_dict: SearchParams, expected_nb_of_result: int) -> None:
        paginator = ScenarioService.search(search_dict).to_dto()
        self.assertEqual(paginator.total_number_of_items, expected_nb_of_result)
