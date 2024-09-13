

from gws_core.core.classes.search_builder import SearchParams
from gws_core.experiment.experiment import Experiment
from gws_core.experiment.experiment_enums import ExperimentStatus
from gws_core.experiment.experiment_service import ExperimentService
from gws_core.folder.space_folder import SpaceFolder
from gws_core.test.base_test_case import BaseTestCase
from gws_core.test.gtest import GTest


# test_experiment_search
class TestExperimentSearch(BaseTestCase):

    def test_search(self):
        experiment_1 = ExperimentService.create_experiment(
            title="My first experiment title world")

        experiment_2: Experiment = ExperimentService.create_experiment(
            title="The second one world")
        experiment_2.mark_as_success()

        folder: SpaceFolder = GTest.create_default_folder()
        experiment_2.folder = folder
        experiment_2.is_validated = True
        experiment_2.save()

        search_dict: SearchParams = SearchParams()

        # Test title search
        search_dict.filtersCriteria = [{"key": "title", "operator": "CONTAINS", "value": "eriment"}]
        self.search(search_dict, 1)

        # Test status search
        search_dict.filtersCriteria = [
            {"key": "status", "operator": "EQ", "value": ExperimentStatus.SUCCESS.value}]
        self.search(search_dict, 1)

        # Test validate search
        search_dict.filtersCriteria = [{"key": "is_validated", "operator": "EQ", "value": True}]
        self.search(search_dict, 1)

        # Test with folder
        search_dict.filtersCriteria = [{"key": "folder", "operator": "IN", "value": [folder.id]}]
        self.search(search_dict, 1)

    def search(self, search_dict: SearchParams, expected_nb_of_result: int) -> None:
        paginator = ExperimentService.search(search_dict).to_dto()
        self.assertEqual(paginator.total_number_of_items, expected_nb_of_result)
